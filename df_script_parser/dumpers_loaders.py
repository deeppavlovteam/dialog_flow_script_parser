from ruamel.yaml import YAML
from math import inf
import re


def enquote_string(string: str) -> str:
    """Enquote a string."""
    return "'" + re.sub(r"\n[ \t]*", "", string).replace("'", r"\'") + "'"


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
    def to_yaml(cls, representer, node):
        return representer.represent_scalar(cls.yaml_tag, node.value)

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(node.value)


class String(StringTag):
    yaml_tag = u"!str"

    def __repr__(self):
        return enquote_string(self.value)


class Python(StringTag):
    yaml_tag = u"!py"


class Start(StringTag):
    yaml_tag = u"!start"


class StartString(Start):
    yaml_tag = u"!start:str"

    def __repr__(self):
        return enquote_string(self.value)


class StartPython(Start):
    yaml_tag = u"!start:py"


class Fallback(StringTag):
    yaml_tag = u"!fallback"


class FallbackString(Fallback):
    yaml_tag = u"!fallback:str"

    def __repr__(self):
        return enquote_string(self.value)


class FallbackPython(Fallback):
    yaml_tag = u"!fallback:py"


yaml_dumper_loader = YAML()

yaml_dumper_loader.register_class(String)
yaml_dumper_loader.register_class(Python)
yaml_dumper_loader.register_class(Start)
yaml_dumper_loader.register_class(StartString)
yaml_dumper_loader.register_class(StartPython)
yaml_dumper_loader.register_class(Fallback)
yaml_dumper_loader.register_class(FallbackString)
yaml_dumper_loader.register_class(FallbackPython)

yaml_dumper_loader.width = inf  # type: ignore
