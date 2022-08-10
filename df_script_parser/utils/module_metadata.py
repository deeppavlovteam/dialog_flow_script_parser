"""Functions to get module metadata."""
import typing as tp
from pathlib import Path
import json
import logging
import importlib.util
import sys
from enum import Enum

from ruamel.yaml.representer import Representer
import pkg_resources

from df_script_parser.utils.exceptions import ModuleNotFoundParserError


class ChangeDir:
    """Change 'sys.path' to include the desired path."""

    index = len(sys.path)

    def __init__(self, path: tp.Union[str, Path]):
        self.path: str = str(Path(path).absolute())

    def __enter__(self):
        sys.path.insert(ChangeDir.index, str(self.path))

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.path.pop(ChangeDir.index)


class ModuleType(Enum):
    """Possible module origin types."""
    PYPI = "pypi"
    SYSTEM = "system"
    LOCAL = "local"

    @classmethod
    def to_yaml(cls, representer: Representer, node: "ModuleType"):
        return representer.represent_data(node.value)


ModuleMetadata = str


def get_metadata(module: str) -> tp.Optional[str]:
    """Get module metadata.

    Return distribution information:

    * For distributions installed via VCS: "{vcs}+{url}@{commit}"
    * For distributions installed via pypi: "{project_name}=={version}"
    * None otherwise

    :param module: str, module name
    :return: Optional[str], module metadata
    """
    # find distribution
    try:
        dist = pkg_resources.get_distribution(module)
    except pkg_resources.DistributionNotFound as e:
        logging.debug(e)
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
    ) as e:
        logging.debug(e)

    # find distribution pypi info
    try:
        return f"{dist.project_name}=={dist.version}"
    except AttributeError as e:
        logging.debug(e)
    return None


def get_location(module: str, inside_dir: str | Path) -> tp.Optional[str]:
    """Get module location.

    :param module: str, Module string used to import it in a script.
    :param inside_dir: str | Path, Directory inside which the script importing module lies.
    :return: str | None, Path to the module being imported.
    """
    directory = Path(inside_dir).absolute()
    project_root_directory = Path(directory.root)
    try:
        package_path = ".".join(list(directory.absolute().relative_to(project_root_directory.absolute()).parts))
    except ValueError as error:
        logging.debug(error)
        return None
    try:
        if not module.startswith("."):
            with ChangeDir(directory):
                spec = importlib.util.find_spec(
                    module
                )
        else:
            with ChangeDir(project_root_directory):
                spec = importlib.util.find_spec(
                    module,
                    package_path
                )
    except ModuleNotFoundError as error:
        logging.debug(error)
        return None

    if spec is None:
        return None
    return spec.origin


def get_module_info(
    module_name: str,
    inside_dir: Path,
    project_root_dir: Path
) -> tp.Tuple[ModuleType, ModuleMetadata]:
    """Return information about module."""
    parent_module = module_name.split('.')[0]

    package_metadata = get_metadata(parent_module)
    if package_metadata is not None:
        return ModuleType.PYPI, package_metadata

    if parent_module in sys.modules:
        return ModuleType.SYSTEM, parent_module

    location = get_location(module_name, inside_dir)
    if location:
        return ModuleType.LOCAL, str(Path(location).absolute())

    raise ModuleNotFoundParserError(f"Not found {module_name} in {inside_dir}.")
