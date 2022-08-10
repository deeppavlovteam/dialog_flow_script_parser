"""Class representing a single python file with all the tools to process it."""

from pathlib import Path
import typing as tp
import libcst as cst

from df_script_parser.utils.namespaces import Namespace
from df_script_parser.processors.parse import Parser

class File:
    """This class represents a single python file."""
    def __init__(self, file: Path, project_root_dir: Path):
        self.file = file
        self.project_root_dir = project_root_dir
        self.module_collection = Namespace(project_root_dir)
        self.dicts = tp.List[dict]
        self.actor_args = None

    def parse(self) -> bool:
        """Parse file contents into modules, dicts and actor call args.

        :return: bool, Whether or not the file follows file format requirements.
        """
        with open(self.file, "r") as file:
            contents = file.read()

        parsed_contents = cst.parse_module(contents)

