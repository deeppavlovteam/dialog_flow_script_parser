from pathlib import Path
import typing as tp
import re
import logging

import libcst as cst

from df_script_parser.processors.parse import Parser
from df_script_parser.utils.namespaces import Namespace, NamespaceTag, RootNamespaceTag
from df_script_parser.utils.module_metadata import ModuleType, ModuleMetadata
from df_script_parser.utils.validators import check_file_structure
from df_script_parser.utils.convenience_functions import get_module_name


class RecursiveParser:
    """Parse multiple files inside project root dir starting with the root file."""
    def __init__(
            self,
            project_root_dir: Path,
    ):
        self.project_root_dir = Path(project_root_dir).absolute()
        self.requirements: tp.List[str] = []
        self.namespaces: tp.Dict[NamespaceTag, Namespace] = {}
        self.unprocessed: tp.List[NamespaceTag] = []

    def process_import(self, module_type: ModuleType, module_metadata: ModuleMetadata):
        if module_type == ModuleType.PYPI and module_metadata not in self.requirements:
            self.requirements.append(module_metadata)
        if module_type == ModuleType.LOCAL:
            module_name = get_module_name(Path(module_metadata), self.project_root_dir)

            if not (NamespaceTag(module_name) in self.namespaces or RootNamespaceTag(module_name) in self.namespaces):

                namespace = self.namespaces[NamespaceTag(module_name)] = Namespace(
                    Path(module_metadata), self.project_root_dir, self.process_import, self.resolve_name
                )

                try:
                    self.fill_namespace_from_file(Path(module_metadata).absolute(), namespace)
                except Exception as error:
                    self.unprocessed.append(NamespaceTag(module_name))
                    logging.warning(f"File {Path(module_metadata)} not included: {error}")

    def resolve_name(self, namespace: str, request: str) -> object:
        pass

    def fill_namespace_from_file(self, file: Path, namespace: Namespace) -> None:
        with open(file, "r") as input_file:
            py_contents = input_file.read()

        parsed_file = cst.parse_module(py_contents)

        transformer = Parser(self.project_root_dir, namespace)

        check_file_structure(parsed_file.visit(transformer))

    def parse_project_dir(self, starting_from_file: Path) -> dict:
        starting_from_file = Path(starting_from_file).absolute()
        namespace = self.namespaces[
            RootNamespaceTag(get_module_name(starting_from_file, self.project_root_dir))
        ] = Namespace(starting_from_file, self.project_root_dir, self.process_import, self.resolve_name)
        self.fill_namespace_from_file(starting_from_file, namespace)
        return self.get_dict()

    def get_dict(self) -> dict:
        return {
            "requirements": self.requirements,
            **{k: v.names for k, v in self.namespaces.items() if k not in self.unprocessed}
        }
