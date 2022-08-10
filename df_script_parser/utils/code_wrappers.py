"""Classes that are used to wrap python code."""
import typing as tp

from ruamel.yaml.representer import Representer
from ruamel.yaml.constructor import Constructor

from df_script_parser.utils.convenience_functions import enquote_string
if tp.TYPE_CHECKING:
    from df_script_parser.utils.namespaces import Namespace


class StringTag:
    yaml_tag = u"!tag"

    def __init__(self, value: str):
        self.value: str = value

    def __hash__(self):
        return self.value.__hash__()

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return False

    @classmethod
    def to_yaml(cls, representer: Representer, node: "StringTag"):
        return representer.represent_scalar(cls.yaml_tag, node.value)

    @classmethod
    def from_yaml(cls, constructor: Constructor, node: "StringTag"):
        return cls(node.value)


class String(StringTag):
    yaml_tag = "!str"

    def __repr__(self):
        return enquote_string(self.value)


class Python(StringTag):
    yaml_tag = "!py"

    def __init__(self, value, namespace: tp.Optional['Namespace'] = None):
        super().__init__(value)
        self.namespace = namespace

    @classmethod
    def to_yaml(cls, representer: Representer, node: "StringTag"):
        return representer.represent_data(node.value)


class Start(StringTag):
    yaml_tag = "!start"


class StartString(Start, String):
    yaml_tag = "!start:str"


class StartPython(Start, Python):
    yaml_tag = "!start:py"


class Fallback(StringTag):
    yaml_tag = "!fallback"


class FallbackString(Fallback, String):
    yaml_tag = "!fallback:str"


class FallbackPython(Fallback, Python):
    yaml_tag = "!fallback:py"
