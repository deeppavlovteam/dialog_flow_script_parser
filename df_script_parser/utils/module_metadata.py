"""This module contains functions that retrieve module metadata.
"""
import typing as tp
from pathlib import Path
import json
import logging
import importlib.util
import sys
from enum import Enum

import pkg_resources

from df_script_parser.utils.exceptions import ModuleNotFoundParserError


class ChangeDir:
    """Changes the :py:data:`sys.path` to include a path. The new path is appended at the
    :py:attr:`ChangeDir.index` position equal to the value of ``len(sys.path)``
    at the moment of :py:mod:`df_script_parser.utils.module_metadata` import.

    :param path: Path to include in :py:data:`sys.path`
    :type path: str | :py:class:`pathlib.Path`
    """

    index = len(sys.path)

    def __init__(self, path: str | Path):
        self.path: str = str(Path(path).absolute())

    def __enter__(self):
        sys.path.insert(ChangeDir.index, str(self.path))

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.path.pop(ChangeDir.index)


class ModuleType(Enum):
    """Types of modules being imported in a script.

    Enums:

    PIP: "pip"
        used for modules that are available via pip such as :py:mod:`df_engine`.

    SYSTEM: "system"
        used for modules listed in :py:data:`sys.stdlib_module_names` such as :py:mod:`sys`.

    LOCAL: "local:
        used for other modules.
    """
    PIP = "pip"
    SYSTEM = "system"
    LOCAL = "local"


def get_metadata(module_name: str) -> tp.Optional[str]:
    """Get distribution metadata.

    :param module_name: Module name
    :type module_name: str

    :return: Distribution metadata:

        - For distributions installed via VCS: ``"{vcs}+{url}@{commit}"``.
        - For distributions installed via pypi: ``"{project_name}=={version}"``.
        - None otherwise.

    :rtype: str, optional
    """
    # find distribution
    try:
        dist = pkg_resources.get_distribution(module_name)
    except pkg_resources.DistributionNotFound as error:
        logging.debug(f"{type(error)}: {error}\nparams:\nmodule={module_name}")
        return None

    # find VCS info
    try:
        vcs_info = json.load((Path(dist.egg_info) / "direct_url.json").open("r"))  # type: ignore
        return f"{vcs_info['vcs_info']['vcs']}+{vcs_info['url']}@{vcs_info['vcs_info']['commit_id']}"
    except (
        AttributeError,
        FileNotFoundError,
        json.decoder.JSONDecodeError,
        KeyError,
    ) as error:
        logging.debug(f"{type(error)}: {error}\nparams:\nmodule={module_name}")

    # find distribution pypi info
    try:
        return f"{dist.project_name}=={dist.version}"
    except AttributeError as error:
        logging.debug(f"{type(error)}: {error}\nparams:\nmodule={module_name}")
    return None


def get_location(
        module_name: str,
        inside_dir: str | Path,
) -> tp.Optional[str]:
    """Get module location.

    :param module_name: Module name.
    :type module_name: str
    :param inside_dir: Parent directory of a script that is importing the module.
    :type inside_dir: str | :py:class:`pathlib.Path`

    :return: Location of the module.
    :rtype: str, optional
    """
    directory = Path(inside_dir).absolute()
    if not module_name.startswith("."):
        try:
            with ChangeDir(directory):
                spec = importlib.util.find_spec(
                    module_name
                )

                if spec is None:
                    return None
                return spec.origin
        except ModuleNotFoundError as error:
            logging.debug(f"{type(error)}: {error}"
                          f"\nparams:\nmodule={module_name}\ninside_dir={inside_dir}")
            return None
    else:
        found_non_empty = False
        dot_split = module_name[1:].split(".")
        for string in dot_split[:-1]:
            if found_non_empty and string == "":
                logging.warning(f"Using double dots after module name is not allowed: {module_name}")
                return None
            if string == "":
                if directory == directory.root:
                    logging.warning(f"Importing {module_name} inside {inside_dir} "
                                    f"refers to a file outside {directory.root}.")
                    return None
                directory = directory.parent
            else:
                found_non_empty = True
                directory = directory / string
        file1 = directory / (dot_split[-1] + ".py")
        file2 = directory / dot_split[-1] / "__init__.py"
        if file1.exists() and file2.exists():
            logging.warning(f"Found two files with the same name: {file1}; {file2}")
        if file1.exists():
            return str(file1.absolute())
        if file2.exists():
            return str(file2.absolute())
        return None


def get_module_info(
        module_name: str,
        inside_dir: str | Path,
        project_root_dir: str | Path | None = None
) -> tp.Tuple[ModuleType, str]:
    """Get information about module.

    :param module_name: Name of the module.
    :type module_name: str
    :param inside_dir: Parent directory of the script that imports the module.
    :type inside_dir: str | :py:class:`pathlib.Path`
    :param project_root_dir: Root directory of the project. Defaults to None.
    :type project_root_dir: str | :py:class:`pathlib.Path`, optional

    :raises ModuleNotFoundParserError: If the module is not found with the specified params.

    :return: A tuple of two elements. The first one is a :py:class:`ModuleType` instance. The second one is:

        - result of :py:func:`get_metadata` if the first element is :py:attr:`ModuleType.PYPI`.
        - name of the root module if the first element is :py:attr:`ModuleType.SYSTEM`.
        - result of :py:func:`get_location` if the first element is :py:attr:`ModuleType.LOCAL`.
    :rtype: tuple[:py:class:`ModuleType`, str]
    """
    root_module = module_name.split('.')[0]
    location = get_location(module_name, inside_dir)

    if location is None:
        raise ModuleNotFoundParserError(f"Not found {module_name} in {inside_dir}. Project root: {project_root_dir}")

    if root_module != "":
        package_metadata = get_metadata(root_module)
        if package_metadata is not None:
            return ModuleType.PIP, package_metadata

        if root_module in sys.stdlib_module_names:
            return ModuleType.SYSTEM, root_module

    return ModuleType.LOCAL, str(Path(location).absolute())
