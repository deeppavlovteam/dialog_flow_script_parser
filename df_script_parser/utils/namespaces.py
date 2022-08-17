"""Classes representing python module imported in a py script."""
# ToDo: docs
import typing as tp
from pathlib import Path

from ruamel.yaml.constructor import Constructor
import libcst as cst

from df_script_parser.utils.code_wrappers import Python, StringTag, String
from df_script_parser.utils.convenience_functions import get_module_name
from df_script_parser.utils.module_metadata import ModuleType, get_module_info
from df_script_parser.utils.exceptions import ObjectNotFoundError, ResolutionError, RequestParsingError
from df_script_parser.utils.convenience_functions import evaluate


class Import(Python):
    yaml_tag = "!import"

    def __init__(self, module):
        super().__init__(module, show_yaml_tag=True)


class From(Python):
    yaml_tag = "!from"

    def __init__(self, module_name: str, obj: str):
        super().__init__(module_name + " " + obj, f"{module_name}.{obj}", True)
        self.module_name = module_name
        self.obj = obj

    @classmethod
    def from_yaml(cls, constructor: Constructor, node: "StringTag"):
        split = node.value.split(" ")
        return cls(split[0], split[1])


class AltName(Python):
    pass


class NamespaceTag(StringTag):
    yaml_tag = "!namespace"

    def __init__(self, value: str, show_yaml_tag: bool = False):
        super().__init__(value, show_yaml_tag)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, NamespaceTag):
            return self.value == other.value
        return False


class Request:
    """Parses a CSTNode as attribute and dictionary requests.

    EXAMPLE
    -------
    a.b.c[d.e.f[2]]['h'][1] ->

    self.attributes = [a, b, c]
    self.indices = [
        Request(attributes=[d, e, f], indices=[2]),
        'h',
        1
    ]
    """
    def __init__(
            self,
            node: cst.CSTNode,
            get_absolute_attributes: tp.Optional[tp.Callable[[tp.List[Python]], tp.List[Python]]] = None
    ):
        self.attributes: tp.List[Python] = []
        self.indices: tp.List['Request' | Python | String] = []
        self.get_absolute_attributes = get_absolute_attributes
        self._process_node(node)
        if get_absolute_attributes:
            self.attributes = get_absolute_attributes(self.attributes)

    def _process_node(self, node: cst.CSTNode):
        if isinstance(node, cst.Subscript):
            self._process_subscript(node)
        elif isinstance(node, cst.Attribute):
            self._process_attribute(node)
        elif isinstance(node, cst.Name):
            self._process_name(node)
        else:
            # Note: If there are a lot of calls to evaluate and they hinder performance it's probably here.
            raise RequestParsingError(f"Node {evaluate(node)} is not a subscript, attribute or name.")

    def _process_subscript(self, node: cst.Subscript):
        if len(node.slice) != 1:
            raise RequestParsingError(f"Subscript {evaluate(node)} has multiple slices.")
        index = node.slice[0].slice
        if not isinstance(index, cst.Index):
            raise RequestParsingError(f"Slice {evaluate(index)} is not an index.")
        try:
            self.indices.insert(0, Request(index.value, self.get_absolute_attributes))
        except RequestParsingError:
            if isinstance(index.value, cst.SimpleString):
                self.indices.insert(0, String(index.value.evaluated_value))
            else:
                self.indices.insert(0, Python(evaluate(index.value)))
        self._process_node(node.value)

    def _process_attribute(self, node: cst.Attribute):
        self._process_node(node.value)
        self._process_node(node.attr)

    def _process_name(self, node: cst.Name):
        self.attributes.append(Python(node.value))

    @classmethod
    def from_str(
            cls,
            request: str,
            get_absolute_attributes: tp.Optional[tp.Callable[[tp.List[Python]], tp.List[Python]]] = None
    ):
        return cls(cst.parse_expression(request), get_absolute_attributes)

    def __repr__(self):
        return "".join([
            ".".join(map(repr, self.attributes)),
            "[" if len(self.indices) > 0 else "",
            "][".join(map(repr, self.indices)),
            "]" if len(self.indices) > 0 else ""
        ])


class Namespace:
    """Collection of names with name resolution."""
    def __init__(
            self,
            path: Path,
            project_root_dir: Path,
            import_module_hook: tp.Callable[[ModuleType, str], None],
    ):
        """

        :param Path path: Path to the python file the namespace of which is being collected.
        :param project_root_dir:
        :param import_module_hook:
        """
        self.path = Path(path)
        self.project_root_dir = Path(project_root_dir)
        self.name: str = get_module_name(self.path, self.project_root_dir)
        self.names: tp.Dict[Python, Import | From | Python | dict] = {}
        self.import_module_hook = import_module_hook

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
            alias: str | None = None,
    ) -> None:
        """Add import to the namespace

        :param module_name: str, String used to import a module
        :param alias: str | None, Alias under which the module is imported
        :return: None
        """
        import_object = Import(self.process_module_import(module_name))
        self.names[
            Python(alias) if alias else Python(module_name)
        ] = import_object

    def add_from_import(
            self,
            module_name: str,
            obj: str,
            alias: str | None = None,
    ) -> None:
        """Add a from-import to the namespace.

        :param module_name: str, Name of the module from which the object is imported
        :param obj: str, Name of the object
        :param alias: str | None, Alias under which the object is imported
        :return: None
        """
        import_object = From(self.process_module_import(module_name), obj)
        self.names[
            Python(alias) if alias else Python(obj)
        ] = import_object

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
        if Python(obj) not in self:
            raise ObjectNotFoundError(f"Not found {obj} in {self.names}")
        self.names[Python(alias)] = AltName(obj)

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

    def get_absolute_name(self, name: str) -> str | None:
        """Make a name namespace-independent.

        EXAMPLE
        -------
        Namespace = 'from Keywords import GLOBAL as gl'

        get_absolute_name(gl, namespace) = 'Keywords.GLOBAL'

        :param name:
        :return:
        """
        try:
            return repr(Request.from_str(name, self.get_absolute_name_list))
        except ResolutionError:
            return None

    def get_absolute_name_list(self, names: tp.List[Python]) -> tp.List[Python]:
        """Modify parsed cst.Attribute or cst.Name to be namespace-independent.

        :param names:
        :return:
        """
        stack = []
        for item in names:
            stack.append(item)
            name = Python(".".join(map(repr, stack)))
            if name in self:
                obj = self.names[name]
                names_left = names[len(stack):]
                while isinstance(obj, AltName):
                    name = obj
                    obj = self.names[name]
                if isinstance(obj, From):
                    return list(map(Python, obj.module_name.split(".") + obj.obj.split("."))) + names_left
                if isinstance(obj, Import):
                    return list(map(Python, obj.value.split("."))) + names_left
                if isinstance(obj, dict):
                    if len(stack) != len(names):
                        raise ResolutionError(
                            f"Attempted access to an attribute {'.'.join(map(repr, names_left))} of a dict {obj}"
                        )
                    return list(map(Python, self.name.split("."))) + [name]
        raise ObjectNotFoundError(f"Not found object {'.'.join(map(repr, names))} in {self.names}")
