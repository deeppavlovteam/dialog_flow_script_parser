"""Processors for dicts.
The purpose of these processors is to take a dictionary
and replace all the keys and values that are not dicts, lists or tuples with StringTag instances.
"""
import re
import typing as tp
from collections import OrderedDict
from os import devnull

import libcst as cst
from pyflakes.api import check
from pyflakes.reporter import Reporter

from df_script_parser.utils.code_wrappers import (
    String,
    Python,
)
from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.exceptions import StarredError
from df_script_parser.utils.namespaces import Namespace


class NodeProcessor:
    def __init__(
            self,
            namespace: Namespace,
            parse_tuples: bool = False,
    ):
        """Process :py:class:`.Dict`. Return a python object

        :param namespace: Namespace used to determine if a tag is needed.
        :type namespace: :py:class:`.Namespace`
        :param parse_tuples: If true parse tuples as well, defaults to False
        :type parse_tuples: bool
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
                return String(value, show_yaml_tag=False)

        value = re.sub(r"\n[ \t]*", "", evaluate(node))

        return Python(value, self.namespace.get_absolute_name(value))

    def __call__(self, node: cst.CSTNode):
        return self._process_node(node)


class Disambiguator:
    """Class that processes a dict by replacing :py:class:`str` with a subclass of :py:class:`.StringTag`

    To determine whether the string should be a :py:class:`.Python` or a :py:class:`.String` object uses a list of
    names in the namespace
    """

    def __init__(self):
        self.names: tp.List[str] = []
        self.replace_lists_with_tuples: bool = False

    def add_name(self, name: str):
        """Add a name to the list of names in a namespace

        :param name: Name to add
        :type name: str
        :return: None
        """
        self.names.append(name)

    def _process_dict(self, obj: dict) -> dict:
        result = OrderedDict()
        for key in obj:
            result[self._process(key)] = self._process(obj[key])
        return dict(result)

    def _process_list(self, obj: list) -> list | tuple:
        result = []
        for element in obj:
            result.append(self._process(element))
        if self.replace_lists_with_tuples:
            return tuple(result)
        return result

    def _process(self, obj: tp.Any) -> tp.Any:
        if isinstance(obj, dict):
            return self._process_dict(obj)
        if isinstance(obj, list):
            return self._process_list(obj)
        if isinstance(obj, str):
            return Python(obj) if is_correct(self.names, obj) else String(obj)
        return obj

    def __call__(self, node: tp.Any):
        return self._process(node)


def is_correct(names: tp.List[str], code: str) -> bool:
    """Check code for correctness if names are available in the namespace.

    :param names: Namespace in which the correctness is asserted
    :type names: list[str]
    :param code: String to check for correctness
    :type code: str
    :return: Whether code is a correct python code
    :rtype: bool
    """
    code_string = "\n".join([*(f"import {name}\n{name}" for name in names), code])
    with open(devnull, "w") as null:
        return check(code_string, "", Reporter(null, null)) == 0
