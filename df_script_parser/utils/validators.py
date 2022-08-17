"""This file contains two functions that make sure parsed files are correct:

1. `check_file_structure` is used to check that file does not have any unsupported nodes
2. `validate_path` is used to check that keys inside the script have correct types
"""
import re
import typing as tp

import libcst as cst
from df_engine.core.keywords import Keywords

from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.exceptions import WrongFileStructure, ScriptValidationError
from df_script_parser.utils.code_wrappers import Python, String


keywords_dict = {k: [
    Python(k, "df_engine.core.keywords." + k),
    Python(k, "df_engine.core.keywords.Keywords." + k)
] for k in Keywords.__members__}

keywords_list = list(map(
    lambda x: Python(x, "df_engine.core.keywords." + x),
    Keywords.__members__
)) + list(map(
    lambda x: Python(x, "df_engine.core.keywords.Keywords." + x),
    Keywords.__members__
))


def check_file_structure(node: cst.CSTNode) -> None:
    """Check that node is empty.

    The `df_script_parser.processors.parse.Parse` used to parse files removes supported nodes it encounters.
    This function makes sure that there are no unsupported nodes in a file by checking that the resulting node is empty.

    :param CSTNode node: Node to check
    :raise WrongFileStructureError: If the node is not empty. Message includes the first unsupported line of code.
    """
    remaining_file = evaluate(node)

    if re.fullmatch(r"[ \t\n\r]*", remaining_file) is None:
        first_non_empty_line = next(line for line in remaining_file.split("\n") if line)
        raise WrongFileStructure(
            f"""File must contain only imports, dict declarations and Actor calls.
            The first line of other type found: {first_non_empty_line}"""
        )


def validate_path(
        traversed_path: tp.List[Python | String],
        final_value: tp.Optional[Python | String] = None
) -> None:
    """Validate a sequence of keys in a script.

    :param traversed_path:
    :param final_value:
    :return:
    """
    if len(traversed_path) < 1:
        raise ScriptValidationError(f"No keys in a traversed path.\n"
                                    f"Keys point to: {final_value}")
    if traversed_path[0] in keywords_dict["GLOBAL"]:
        if len(traversed_path) < 2:
            raise ScriptValidationError(f"Less than 2 consecutive keys in a script: {traversed_path}.\n"
                                        f"Keys point to: {final_value}")
        if traversed_path[1] not in keywords_list:
            raise ScriptValidationError(f"GLOBAL keys should be keywords: {traversed_path}")
    else:
        if len(traversed_path) < 3:
            raise ScriptValidationError(f"Less than 3 consecutive keys in a script: {traversed_path}.\n"
                                        f"Keys point to: {final_value}")
        if traversed_path[2] not in keywords_list:
            raise ScriptValidationError(f"Node keys should be keywords: {traversed_path}")
