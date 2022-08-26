"""This module contains a parser that recursively parses all the files imported in a root file
"""
import logging
import typing as tp
from pathlib import Path

import libcst as cst

from df_script_parser.processors.parse import Parser
from df_script_parser.utils.code_wrappers import Python, String
from df_script_parser.utils.convenience_functions import get_module_name
from df_script_parser.utils.exceptions import (
    KeyNotFoundError,
    NamespaceNotParsedError,
    ObjectNotFoundError,
    ResolutionError,
    ParserError,
    ScriptValidationError,
)
from df_script_parser.utils.module_metadata import ModuleType
from df_script_parser.utils.namespaces import Namespace, NamespaceTag, Request, Import
from df_script_parser.utils.validators import check_file_structure, validate_path


class RecursiveParser:
    """Parse multiple files inside project root dir starting with the root file

    :param project_root_dir: Root directory of a project
    :type project_root_dir: :py:class:`pathlib.Path`
    """

    def __init__(
            self,
            project_root_dir: Path,
    ):
        self.project_root_dir = Path(project_root_dir).absolute()
        self.requirements: tp.List[str] = []
        self.namespaces: tp.Dict[NamespaceTag, Namespace] = {}
        self.unprocessed: tp.List[NamespaceTag] = []
        self.script: tp.Optional[Python] = None
        self.start_label: tp.Optional[tp.Tuple[Python | String]] = None
        self.fallback_label: tp.Optional[tp.Tuple[Python | String]] = None

    def get_object(self, request: Request) -> object:
        """Return an object requested in ``request``

        :param request: Request of an object
        :type request: :py:class:`df_script_parser.utils.namespaces.Request`
        :return: Object requested in a ``request``

        :raise :py:exc:`df_script_parser.exceptions.ObjectNotFoundError`:
            If a requested object is not found
        """
        for i in reversed(range(1, len(request.attributes))):
            try:
                left = request.attributes[:i]
                middle = request.attributes[i]
                right = request.attributes[i + 1:]
                potential_namespace = NamespaceTag(".".join(map(repr, left)))
                namespace = self.namespaces.get(potential_namespace)
                if namespace is None:
                    raise NamespaceNotParsedError(
                        f"Not found namespace {repr(potential_namespace)}, request={request}"
                    )
                name = namespace.names.get(middle)
                if name is None:
                    raise ObjectNotFoundError(
                        f"Not found {request.attributes[-1]} in {potential_namespace}, request={request}"
                    )
                if isinstance(name, Python):
                    name = self.get_object(Request.from_str(
                        ".".join([
                            name.absolute_value,
                            *map(repr, right)
                        ])
                    ))
                return name
            except ResolutionError as error:
                logging.debug("Name not found reason: %s", error)
        raise ResolutionError(f"Cannot find object {request}")

    def traverse_dict(
            self,
            script: tp.Dict[Python | String, dict | Python | String],  # ToDo: Introduce a type for values.
            func: tp.Callable[[tp.List[Python | String], Python | String], None],
            traversed_path: tp.List[Python | String] = []
    ):
        """Traverse a dictionary as a tree call ``func`` at leaf nodes of a tree

        :param script: Dictionary to traverse
        :param func: Function to be called
        :type func:
            Callable[[list[:py:class:`Python` | :py:class:`String`], :py:class:`Python` | :py:class:`String`], None]
        :param traversed_path: Path to the current node
        :return: None
        """
        for key in script:
            value = script[key]
            while isinstance(value, Python):
                try:
                    value = self.get_object(Request.from_str(value.absolute_value))
                except ResolutionError:
                    logging.debug(f"Cannot resolve request: {value.absolute_value}")
                    break
            if isinstance(value, dict):
                self.traverse_dict(value, func, traversed_path + [key])
            else:
                func(traversed_path + [key], value)

    def check_node_existence(
            self,
            request: Request
    ) -> tp.Union[Import, dict, Python]:
        """Retrieve a dict behind the request

        :param request: Request to the dict
        :return:
        """
        name = self.get_object(request)
        for key in request.indices:
            if isinstance(name, Python):
                name = self.check_node_existence(
                    Request.from_str(name.absolute_value)
                )
            if not isinstance(name, dict):
                raise ResolutionError(f"Object {name} is not a dict.")
            if isinstance(key, Request):
                key = Python("", repr(key))
            if key not in name:
                raise KeyNotFoundError(f"Not found {key} in {name}")
            name = name[key]
        return name

    def check_actor_args(self, actor_args: dict):
        """Checks :py:class:`~df_engine.core.actor.Actor` args for correctness

        :param actor_args: Arguments of the :py:class:`~df_engine.core.actor.Actor` call
        :type actor_args: dict
        :return: None
        """
        script = actor_args.get("script")
        if script is None:
            raise ScriptValidationError("Actor call should have a ``script`` argument")
        start_label = actor_args.get("start_label")
        if start_label is None:
            raise ScriptValidationError("Actor call should have a ``start_label`` argument")
        fallback_label = actor_args.get("fallback_label")

        if not isinstance(script, Python):
            raise RuntimeError(f"Script argument in actor is not a Python instance: {script}")
        script_request = Request.from_str(script.absolute_value)
        script = self.get_object(script_request)
        if not isinstance(script, dict):
            raise RuntimeError(f"Script is not a dict: {script}")

        self.traverse_dict(script, validate_path)

        for label in [start_label, fallback_label]:
            if label:
                if not isinstance(label, tuple):
                    raise RuntimeError(f"Label is not a tuple: {label}")
                script_request.indices = list(label)
                self.check_node_existence(script_request)

    def process_import(self, module_type: ModuleType, module_metadata: str):
        """Import module hook for Namespace.

        Adds distribution metadata to requirements. Parses local files.

        :param module_type:
        :param module_metadata:
        :return:
        """
        if module_type == ModuleType.PIP and module_metadata not in self.requirements:
            self.requirements.append(module_metadata)
        if module_type == ModuleType.LOCAL:
            module_name = get_module_name(Path(module_metadata), self.project_root_dir)

            tag = NamespaceTag(module_name, module_name.removesuffix(".__init__"))

            if tag not in self.namespaces:

                namespace = self.namespaces[tag] = Namespace(
                    Path(module_metadata), self.project_root_dir, self.process_import, self.check_actor_args
                )

                try:
                    self.fill_namespace_from_file(Path(module_metadata).absolute(), namespace)
                    logging.info(f"Added namespace {namespace.name}")
                except ParserError as error:
                    self.unprocessed.append(tag)
                    logging.warning(f"File {Path(module_metadata)} not included: {error}")

    def fill_namespace_from_file(self, file: Path, namespace: Namespace) -> Parser:
        """Parse a file, add its contents to a namespace.

        :param file:
        :param namespace:
        :return:
        """
        with open(file, "r") as input_file:
            py_contents = input_file.read()
        # ToDo: add pyflake check

        parsed_file = cst.parse_module(py_contents)

        transformer = Parser(self.project_root_dir, namespace)

        check_file_structure(parsed_file.visit(transformer))
        return transformer

    def parse_project_dir(self, starting_from_file: Path) -> dict:
        """Parse a file, mark it as a Root file.

        :param starting_from_file:
        :return:
        """
        starting_from_file = Path(starting_from_file).absolute()
        module_name = get_module_name(starting_from_file, self.project_root_dir)

        tag = NamespaceTag(module_name, module_name.removesuffix(".__init__"))
        namespace = self.namespaces[
            tag
        ] = Namespace(starting_from_file, self.project_root_dir, self.process_import, self.check_actor_args)

        self.fill_namespace_from_file(starting_from_file, namespace)

        return self.to_dict()

    def to_dict(self) -> dict:
        return {
            "requirements": self.requirements,
            "namespaces": {k: v.names for k, v in self.namespaces.items() if k not in self.unprocessed}
        }
