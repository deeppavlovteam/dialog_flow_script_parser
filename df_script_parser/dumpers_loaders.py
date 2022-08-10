from math import inf

from ruamel.yaml import YAML

from df_script_parser.utils.code_wrappers import String, Python, Start, StartString, StartPython, Fallback, FallbackString, FallbackPython
from df_script_parser.utils.namespaces import NamespaceTag, RootNamespaceTag, From, Import


yaml_dumper_loader = YAML()

yaml_dumper_loader.register_class(String)
yaml_dumper_loader.register_class(Python)
yaml_dumper_loader.register_class(Start)
yaml_dumper_loader.register_class(StartString)
yaml_dumper_loader.register_class(StartPython)
yaml_dumper_loader.register_class(Fallback)
yaml_dumper_loader.register_class(FallbackString)
yaml_dumper_loader.register_class(FallbackPython)
yaml_dumper_loader.register_class(NamespaceTag)
yaml_dumper_loader.register_class(RootNamespaceTag)
yaml_dumper_loader.register_class(From)
yaml_dumper_loader.register_class(Import)

yaml_dumper_loader.width = inf  # type: ignore
