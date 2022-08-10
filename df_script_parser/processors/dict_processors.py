"""Processors for dicts.
The goal of these processors is to take a dictionary
and replace all the keys and values that are not dicts, lists or tuples with StringTag instances."""
import logging
import typing as tp
import re
from os import devnull
from collections import OrderedDict

import libcst as cst
from pyflakes.api import check
from pyflakes.reporter import Reporter

from df_script_parser.utils.namespaces import Namespace
from df_script_parser.utils.exceptions import StarredError
from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.code_wrappers import (
    String,
    Python,
    Start,
    Fallback,
    StartString,
    FallbackString,
    StartPython,
    FallbackPython,
)


class NodeProcessor:
    def __init__(
        self,
        namespace: Namespace,
        parse_tuples: bool = False,
    ):
        """Process cst.Dict. Return a python object.

        :param start_node: CSTNode, Node to process
        :param imports: List[str], List of lines of code with import statements preceding the node
        :param start_label: List[Any], List of dictionary keys, represents a path to the start node
        :param fallback_label: List[Any], List of dictionary keys, represents a path to the fallback node
        :param parse_tuples: bool, If true parse tuples as well
        :param safe_mode: bool, If false doesn't check for ambiguity.
         Set to false only if there are no strings in your code that have the value that might be python code.
        """
        self.namespace: Namespace = namespace
        self.parse_tuples = parse_tuples

    def _process_dict(self, node: cst.Dict) -> dict:
        result = OrderedDict()
        for element in node.elements:
            if not isinstance(element, cst.DictElement):
                raise StarredError("Starred dict elements are not supported")
            key = self._process_node(element.key)
            result[key] = self._process_node(element.value)
        return dict(result)

    def _process_list(self, node: cst.List | cst.Tuple) -> list:
        result = []
        for element in node.elements:
            if not isinstance(element, cst.Element):
                raise StarredError("Starred elements are not supported")
            result.append(self._process_node(element.value))
        return result

    def _process_node(self, node: cst.CSTNode) -> tp.Any:
        """Process a node. Return a python object.

        Processing rules:

        * If a node is a dictionary
            return a dict with its keys and values processed.
        * If a node is a list
            return a list with its values processed.
        * If a node is a tuple and self.parse_tuples
            return a tuple with its values processed.
        * If a node is a BasicString and self.safe_mode
            check for string ambiguity -- check if the string could be python code.
            If it could return a String instance.
            Also check if the string is a start or a fallback node.
            Return an instance of the Start or the Fallback class.
            Return a string otherwise
        * Otherwise check if the node could be a start or fallback node.
            If so return an instance of the Start or Fallback class else return a str.
        """
        if isinstance(node, cst.Dict):
            return self._process_dict(node)

        if isinstance(node, cst.List):
            return self._process_list(node)

        if self.parse_tuples and isinstance(node, cst.Tuple):
            return tuple(self._process_list(node))

        if isinstance(node, cst.SimpleString):
            value = node.evaluated_value
            if is_correct(list(self.namespace), value):
                return String(value)
        else:
            value = re.sub(r"\n[ \t]*", "", evaluate(node))

        return Python(value)

    def __call__(self, node: cst.CSTNode):
        return self._process_node(node)


class Disambiguator:
    def __init__(self, script: dict, imports: tp.List[str]):
        """Process a dict. Return a dict with strings replaced with a subclass of StringTag.
        Store a start_label and a fallback_label paths if a corresponding StringTag was found.

        :param imports: List[str], List of lines of code with import statements which are used to determine a subclass
        """
        self.imports = imports
        self.stack: tp.List[tp.Any] = []
        self.start_label: tp.Optional[tp.List[tp.Any]] = None
        self.fallback_label: tp.Optional[tp.List[tp.Any]] = None
        self.result = self._convert(script)

    def _convert(self, obj: tp.Any) -> tp.Any:
        """Recursively replace all str instances inside os an obj with a correct StringTag subclass instance.

        Replacement rules:

        * If obj is a dict
            return a dict with all of its keys and values converted.
        * If obj is a list
            return a list with all of its values converted.
        * If obj is an instance of Start of Fallback classes or their subclasses
            store current path (as given by self.stack) in either self.start_label or self.fallback_label
        * If obj is an instance of str or Start or Fallback classes
            return either an instance of String or Python class or their subclasses.
            * If the string is a correct python code given self.imports
                return a Python or its subclass instance else return a String or its subclass instance.
        """
        # ordered dict
        if isinstance(obj, dict):
            result = OrderedDict()
            for key in obj.keys():
                new_key = self._convert(key)
                self.stack.append(new_key)
                # validate_stack(self.stack)
                result[new_key] = self._convert(obj[key])
                self.stack.pop()
            return dict(result)

        # list
        if isinstance(obj, list):
            result = []
            for el in obj:
                result.append(self._convert(el))
            return result

        # str
        if isinstance(obj, str):
            return Python(obj) if is_correct(self.imports, obj) else String(obj)

        # start
        if isinstance(obj, Start):
            if not isinstance(obj, (StartString, StartPython)):
                obj = StartPython(obj.value) if is_correct(self.imports, obj.value) else StartString(obj.value)
            self.start_label = self.stack + [obj]
            return obj

        # fallback
        if isinstance(obj, Fallback):
            if not isinstance(obj, (FallbackString, FallbackPython)):
                obj = FallbackPython(obj.value) if is_correct(self.imports, obj.value) else FallbackString(obj.value)
            self.fallback_label = self.stack + [obj]
            return obj

        return obj


def is_correct(names: tp.List[str], code: str) -> bool:
    """Check code for correctness if names are available in the namespace.

    :param List[str] names: List of the names in the namespace (which may be referenced in the code)
    :param str code: String to check for correctness
    :return: Whether code is a correct python code
    :rtype: bool
    """
    code_string = "\n".join([*(f"import {name}\n{name}" for name in names), code])
    with open(devnull, "w") as null:
        return check(code_string, "", Reporter(null, null)) == 0
