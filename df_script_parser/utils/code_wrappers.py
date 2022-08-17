"""Classes that are used to wrap python code."""
from abc import ABC

from ruamel.yaml.representer import Representer
from ruamel.yaml.constructor import Constructor

from df_script_parser.utils.convenience_functions import enquote_string


class StringTag(ABC):
    yaml_tag = u"!tag"

    def __init__(self, value: str, add_tag: bool = True):
        self.value: str = value
        self.add_tag = add_tag

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    @classmethod
    def to_yaml(cls, representer: Representer, node: "StringTag"):
        if node.add_tag:
            return representer.represent_scalar(cls.yaml_tag, node.value)
        else:
            return representer.represent_data(node.value)

    @classmethod
    def from_yaml(cls, constructor: Constructor, node: "StringTag"):
        return cls(node.value)


class String(StringTag):
    yaml_tag = "!str"

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, String):
            return self.value == other.value
        return False

    def __repr__(self):
        return enquote_string(self.value)


class Python(StringTag):
    yaml_tag = "!py"

    def __init__(self, display_value: str, absolute_value: str | None = None, show_yaml_tag: bool = False):
        super().__init__(display_value, show_yaml_tag)
        self.absolute_value = absolute_value or display_value

    def __hash__(self):
        return hash(self.absolute_value)

    def __eq__(self, other):
        if isinstance(other, Python):
            return self.absolute_value == other.absolute_value
        return False
