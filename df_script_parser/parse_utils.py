import logging
import libcst as cst
import typing as tp
from pathlib import Path
import sys
import collections
from .distribution_metadata import get_metadata, get_location
import re


def evaluate(node: cst.CSTNode) -> str:
    """Evaluate cst Node.

    :param node: cst.Node
    :return: string representing node
    """
    return cst.parse_module("").code_for_node(node)


class ImportBlock:
    """Block of code with import statements."""

    class ChangeDir:
        """Change 'sys.path' to include the desired path."""

        def __init__(self, path: tp.Union[str, Path]):
            self.path: tp.Union[str, Path] = path

        def __enter__(self):
            sys.path.insert(0, str(self.path))

        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.path.pop(0)

    def __init__(self, working_dir: tp.Union[str, Path]):
        self.imports: tp.Dict[str, tp.DefaultDict[str, tp.List[str]]] = {
            "pypi": collections.defaultdict(list),
            "system": collections.defaultdict(list),
            "local": collections.defaultdict(list),
        }
        self.modules: tp.Dict[str, list] = {}
        self.working_dir: tp.Union[str, Path] = working_dir
        logging.debug(f"Created ImportBlock with working_dir={working_dir}")

    def _find_module(self, module: str) -> list:
        with ImportBlock.ChangeDir(self.working_dir):
            parent_module = module.split(".")[0]

            # find vcs or pypi info
            metadata = get_metadata(parent_module)

            if metadata is not None:
                return self.imports["pypi"][metadata]

            # find modules in system modules
            if parent_module in sys.modules.keys():
                return self.imports["system"][parent_module]

            # find locally installed modules
            location = get_location(module, self.working_dir)
            if location:
                return self.imports["local"][location]

            raise RuntimeError(
                f"Module {module} not found in neither {self.working_dir}" f" nor system modules nor installed packages"
            )

    def _add_import(self, module: str, code: str) -> None:
        """Add import to self.imports.

        Add (key, value) pair to the dict:

        * self.imports["pypi"] if the module is available via pip.
        * self.imports["system"] if the module is in 'sys.modules'.
        * self.imports["local"] if the module is stored locally.

        Added key is additional information about module:

        * "pypi": package information, e.g., "df_engine==0.9.0".
        * "system": module name.
        * "local": path to the file. The path is relative to the self.working_dir if possible, absolute otherwise.

        Added value is the line of code that imports the module.

        :param module: str, Name of the module to import, e.g., df_engine.
        :param code: str, Code that imports the module

        :return: None
        """
        if module not in self.modules.keys():
            self.modules[module] = self._find_module(module)
        self.modules[module].append(re.sub(r"\n[ \t]*|\(|\)", "", code).strip(",").replace(",", ", "))
        return

    def append(self, node: cst.CSTNode):
        if isinstance(node, cst.Import):
            for name in node.names:
                code = evaluate(cst.Import(names=[name.with_changes(comma=cst.MaybeSentinel.DEFAULT)]))
                self._add_import(name.evaluated_name, code)
        elif isinstance(node, cst.ImportFrom):
            if isinstance(node.names, cst.ImportStar):
                raise RuntimeError(f"ImportStar is not allowed: {evaluate(node)}")
            if node.module:
                code = evaluate(node)
                self._add_import(evaluate(node.module), code)
            else:
                for name in node.names:
                    code = evaluate(cst.Import(names=[name.with_changes(comma=cst.MaybeSentinel.DEFAULT)]))
                    self._add_import(name.evaluated_name, code)
        else:
            raise TypeError(f"Not an import: {evaluate(node)}")

    def get_dict(self) -> dict:
        return dict(
            pypi=dict(self.imports["pypi"]),
            system=dict(self.imports["system"]),
            local=dict(self.imports["local"]),
        )

    def __iter__(self):
        for key in self.imports.keys():
            for module in self.imports[key].keys():
                for code in self.imports[key][module]:
                    yield code
