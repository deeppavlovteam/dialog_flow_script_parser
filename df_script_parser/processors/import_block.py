import re
import typing as tp
from pathlib import Path
import collections

import libcst as cst

from df_script_parser.utils.module_metadata import ModuleType, ModuleMetadata, get_module_info
from df_script_parser.utils.exceptions import StarredError
from df_script_parser.utils.convenience_functions import evaluate


class ImportBlock:
    """Block of code with import statements."""

    def __init__(self, file: Path, project_root_dir: Path):
        self.imports: tp.Dict[ModuleType, tp.DefaultDict[ModuleMetadata, tp.List[str]]] = {
            ModuleType.SYSTEM: collections.defaultdict(list),
            ModuleType.PYPI: collections.defaultdict(list),
            ModuleType.LOCAL: collections.defaultdict(list),
        }
        self.module_metadata: tp.Dict[str, tp.Tuple[ModuleType, ModuleMetadata]] = {}
        self.file: Path = Path(file)
        self.project_root_dir = Path(project_root_dir)

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
        if module not in self.module_metadata:
            self.module_metadata[module] = get_module_info(module, self.file.parent, self.project_root_dir)
        module_type, module_metadata = self.module_metadata[module]
        self.imports[module_type][module_metadata].append(re.sub(r"\n[ \t]*|\(|\)", "", code).strip(",").replace(",", ", "))
        return

    def append(self, node: tp.Union[cst.Import, cst.ImportFrom]):
        if isinstance(node, cst.Import):
            for name in node.names:
                code = evaluate(cst.Import(names=[name.with_changes(comma=cst.MaybeSentinel.DEFAULT)]))
                self._add_import(name.evaluated_name, code)
        elif isinstance(node, cst.ImportFrom):
            if isinstance(node.names, cst.ImportStar):
                raise StarredError(f"ImportStar is not allowed: {evaluate(node)}")
            if node.module:
                code = evaluate(node)
                self._add_import(evaluate(node.module), code)
            else:
                for name in node.names:
                    code = evaluate(cst.Import(names=[name.with_changes(comma=cst.MaybeSentinel.DEFAULT)]))
                    self._add_import(name.evaluated_name, code)

    def get_dict(self) -> dict:
        return dict(
            system=dict(self.imports[ModuleType.SYSTEM]),
            pypi=dict(self.imports[ModuleType.PYPI]),
            local=dict(self.imports[ModuleType.LOCAL]),
        )

    def __iter__(self):
        for key in self.imports:
            for module in self.imports[key]:
                for code in self.imports[key][module]:
                    yield code
