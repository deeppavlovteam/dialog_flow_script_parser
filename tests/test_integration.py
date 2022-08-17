"""Test parser as a whole."""
from pathlib import Path
from io import StringIO

import pytest

from df_script_parser.processors.recursive_parser import RecursiveParser
from df_script_parser.dumpers_loaders import yaml_dumper_loader
from df_script_parser.utils.exceptions import WrongFileStructure, ScriptValidationError, KeyNotFoundError


@pytest.mark.parametrize(
    "project_root_dir,main_file,script,exception",
    [
        *[
            (
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/py"),
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/py/main.py"),
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/yaml/script.yaml"),
                exception
            ) for test_number, exception in zip(
                range(1, 10),
                [
                    None,
                    WrongFileStructure,
                    ScriptValidationError,
                    None,
                    ScriptValidationError,
                    KeyNotFoundError,
                    ScriptValidationError,
                    None,
                    None
                ]
            )
        ],
        *[
            (
                Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/py"),
                Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/py/main.py"),
                Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/yaml/script.yaml"),
                exception
            ) for test_number, exception in zip(
                range(1, 2),
                [
                    None
                ]
            )
        ],
        (
            Path("examples/example_py2yaml/py"),
            Path("examples/example_py2yaml/py/main.py"),
            Path("examples/example_py2yaml/yaml/script.yaml"),
            None
        )
    ],
)
def test_py2yaml(project_root_dir, main_file, script, exception):
    """Test the py2yaml part of the parser."""
    def _test_py2yaml():
        buffer = StringIO()
        recursive_parser = RecursiveParser(Path(project_root_dir))
        recursive_parser.parse_project_dir(Path(main_file))
        yaml_dumper_loader.dump(recursive_parser.to_dict(), buffer)
        buffer.seek(0)
        with open(script, "r") as correct_result:
            assert buffer.read() == correct_result.read()

    if exception:
        with pytest.raises(exception):
            _test_py2yaml()
    else:
        _test_py2yaml()