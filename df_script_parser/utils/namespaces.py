"""Classes representing python module imported in a py script."""
# ToDo: docs
import typing as tp
from pathlib import Path

from ruamel.yaml.constructor import Constructor

from df_script_parser.utils.code_wrappers import Python, StringTag
from df_script_parser.utils.convenience_functions import get_module_name
from df_script_parser.utils.module_metadata import ModuleType, ModuleMetadata, get_module_info


class Import(StringTag):
    yaml_tag = "!import"


class From(Import):
    yaml_tag = "!from"

    def __init__(self, module_name: str, obj: str):
        super().__init__(module_name + " " + obj)
        self.module_name = module_name
        self.obj = obj

    @classmethod
    def from_yaml(cls, constructor: Constructor, node: "StringTag"):
        split = node.value.split(" ")
        return cls(split[0], split[1])


class NamespaceTag(StringTag):
    yaml_tag = "!namespace"


class RootNamespaceTag(NamespaceTag):
    yaml_tag = "!root"


class Namespace:
    """Collection of names with name resolution."""
    def __init__(
            self,
            path: Path,
            project_root_dir: Path,
            import_module_hook: tp.Callable[[ModuleType, ModuleMetadata], None],
            name_resolution_hook: tp.Callable[[str, str], object],
    ):
        """

        :param Path path: Path to the python file the namespace of which is being collected.
        :param project_root_dir:
        :param import_module_hook:
        :param name_resolution_hook:
        """
        self.path = Path(path)
        self.project_root_dir = Path(project_root_dir)
        self.name = get_module_name(self.path, self.project_root_dir)
        self.names: tp.Dict[Python, Import | From | Python | dict] = {}
        self.import_module_hook = import_module_hook
        self.name_resolution_hook = name_resolution_hook

    def __iter__(self):
        for name in self.names:
            yield name

    def process_module_import(
            self,
            module_name: str,
    ) -> str:
        """Fire the import_module_hook, return alternative import name for local modules

        :param str module_name: Module name as in the file
        :return: module_name if module_type is PYPI or SYSTEM else module name is the result of :func:`get_module_name`
        :rtype: str
        """
        module_type, module_metadata = get_module_info(module_name, self.path.parent, self.project_root_dir)
        self.import_module_hook(module_type, module_metadata)

        return get_module_name(
            Path(module_metadata), self.project_root_dir
        ) if module_type is ModuleType.LOCAL else module_name

    def add_import(
            self,
            module_name: str,
            alias: str | None,
    ) -> None:
        """Add import to the namespace

        :param module_name: str, String used to import a module
        :param alias: str | None, Alias under which the module is imported
        :return: None
        """
        self.names[Python(alias) if alias else Python(module_name)] = Import(self.process_module_import(module_name))

    def add_from_import(
            self,
            module_name: str,
            obj: str,
            alias: str | None,
    ) -> None:
        """Add a from-import to the namespace.

        :param module_name: str, Name of the module from which the object is imported
        :param obj: str, Name of the object
        :param alias: str | None, Alias under which the object is imported
        :return: None
        """
        self.names[Python(alias) if alias else Python(obj)] = From(self.process_module_import(module_name), obj)

    def add_alt_name(
            self,
            obj: str,
            alias: str,
    ) -> None:
        """Add an alternative name to the object in the namespace.

        :param str obj: Object to which the alternative name is bound
        :param str alias: The alternative name
        :return: None?
        """
        self.names[Python(alias)] = Python(obj)

    def add_dict(
            self,
            name: str,
            dictionary: dict
    ) -> None:
        """Add a dictionary to the namespace.

        :param str name: Dictionary name
        :param dict dictionary: Dictionary contents
        :return:
        """
        self.names[Python(name)] = dictionary

    def resolve(self, request: str) -> object:
        """Resolve an object referenced in request.

        :param request:
        :return:
        """
        pass
