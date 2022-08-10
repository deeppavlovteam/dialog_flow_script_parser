"""Different functions to validate objects."""
import re
import typing as tp
from enum import Enum
import logging

import libcst as cst
from df_engine.core.keywords import Keywords

from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.exceptions import WrongFileStructure


def check_file_structure(node: cst.CSTNode) -> None:
    """Check that node is empty (as transformer removes nodes it encounters).

    :param node: CSTNode, Node to check
    """
    remaining_file = evaluate(node)

    if re.fullmatch(r"[ \t\n\r]*", remaining_file) is None:
        raise WrongFileStructure(
            f"File must contain only imports, dict declarations and Actor calls. Found:\n{remaining_file}"
        )


def validate_path(path: tp.List[tp.Any]) -> bool:
    """Validate a path """
    keywords = list(map(Python, list(Keywords.__members__)))
    if len(stack) == 2 and stack[0] == Python("GLOBAL") and stack[1] not in keywords:
        logging.warning(f"GLOBAL keys should be keywords: {stack}")
        return False
    if len(stack) == 3 and stack[0] != Python("GLOBAL") and stack[2] not in keywords:
        logging.warning(f"Node keys should be keywords: {stack}")
        return False

