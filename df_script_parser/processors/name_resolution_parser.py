"""Function for name resolution in namespace."""
import typing as tp

import libcst as cst

from df_script_parser.utils.code_wrappers import Python, String
from df_script_parser.utils.exceptions import RequestParsingError
from df_script_parser.utils.convenience_functions import evaluate


class Request:
    """Parses a CSTNode as a dictionary request."""
    def __init__(self, node: cst.CSTNode):
        self.constant: Python | String | None = None
        self.attributes: tp.List[Python] = []
        self.indices: tp.List['Request'] = []
        self._process_node(node)

    def _process_node(self, node: cst.CSTNode):
        if isinstance(node, cst.Subscript):
            self._process_subscript(node)
        elif isinstance(node, cst.Attribute):
            self._process_attribute(node)
        elif isinstance(node, cst.Name):
            self._process_name(node)
        elif len(self.attributes) + len(self.indices) > 0 and self.constant is not None:
            raise RequestParsingError(f"Tried to process {evaluate(node)}, but request is not empty: {repr(self)}")
        else:
            if isinstance(node, cst.SimpleString):
                self.constant = String(node.evaluated_value)
            else:
                self.constant = Python(evaluate(node))

    def _process_subscript(self, node: cst.Subscript):
        if len(node.slice) != 1:
            raise RequestParsingError(f"Subscript {evaluate(node)} has multiple slices")
        self.indices.insert(0, Request(cst.ensure_type(node.slice[0].slice, cst.Index).value))
        self._process_node(node.value)

    def _process_attribute(self, node: cst.Attribute):
        self._process_node(node.value)
        self._process_node(node.attr)

    def _process_name(self, node: cst.Name):
        self.attributes.append(Python(node.value))

    @classmethod
    def from_str(cls, request: str):
        return cls(cst.parse_expression(request))

    def __repr__(self):
        if len(self.attributes) > 0 and self.constant is not None:
            raise RequestParsingError(f"Request has both attributes: {self.attributes} and a constant: {self.constant}")
        return  "".join([
            repr(self.constant) if self.constant else ".".join(map(repr, self.attributes)),
            "[" if len(self.indices) > 0 else "",
            "][".join(map(repr, self.indices)),
            "]" if len(self.indices) > 0 else ""
        ])
