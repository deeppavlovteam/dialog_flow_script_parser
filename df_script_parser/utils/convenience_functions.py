"""Frequently used short functions."""

import re
from pathlib import Path

import libcst as cst


def evaluate(node: cst.CSTNode | str) -> str:
    """Return string representation of a `libcst.Node`.

    :param node: libcst.Node, Node to evaluate.
    :return: str, string representing node.
    """
    if isinstance(node, str):
        return node
    return cst.parse_module("").code_for_node(node)


def enquote_string(string: str) -> str:
    """Enquote a string.

    Return a string with all `\n`, ` ` and `\t` deleted.
    Escape single quotes inside the string.
    Wrap the string in single quotes.

    :param string: str, String to enquote.
    :return: Enquoted string.
    """
    return "'" + re.sub(r"\n[ \t]*", "", string).replace("'", r"\'") + "'"


def get_module_name(path: Path, project_root_dir: Path) -> str:
    """Get python import string for the file path inside the project_root_dir.

    EXAMPLE
    -------
    dir
    +-- file.py
    +-- package
    +--+-- __init__.py
    +--+-- file.py

    get_module_name("dir/file.py", "dir") = "file"
    get_module_name("dir/package/__init__.py", "dir") = "package"
    get_module_name("dir/package/file.py", "dir") = "package.file"
    get_module_name("dir/package/__init__.py", "dir/package") = "package"
    get_module_name("dir/package/file.py", "dir/package") = "package.file"
    """
    if Path(project_root_dir / "__init__.py").exists():
        project_root_dir = project_root_dir.parent
    path = Path(str(path).rstrip(".py"))
    if str(path).endswith("__init__"):
        path = path.parent
    parts = path.relative_to(project_root_dir).parts
    if len(parts) == 0:
        raise RuntimeError(f"Parts are empty with path={path} and project_root_dir={project_root_dir}")
    return ".".join(parts)
