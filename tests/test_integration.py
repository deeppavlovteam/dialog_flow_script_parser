"""Test parser as a whole."""
from io import StringIO
from pathlib import Path

import pytest

from df_script_parser.dumpers_loaders import yaml_dumper_loader
from df_script_parser.processors.recursive_parser import RecursiveParser
from df_script_parser.utils.exceptions import ScriptValidationError, KeyNotFoundError
from df_script_parser.tools import yaml2py


py2yaml_params = \
[
    *[
        (
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/python_files"),
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/python_files/main.py"),
                Path(f"tests/test_py2yaml/simple_tests/test_{test_number}/yaml_files/script.yaml"),
                exception
        ) for test_number, exception in zip(
            range(1, 11),
            [
                None,
                ScriptValidationError,
                ScriptValidationError,
                None,
                ScriptValidationError,
                KeyNotFoundError,
                ScriptValidationError,
                None,
                None,
                None,
            ]
        )
    ],
    *[
        (
            Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/python_files"),
            Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/python_files/main.py"),
            Path(f"tests/test_py2yaml/complex_tests/test_{test_number}/yaml_files/script.yaml"),
            exception
        ) for test_number, exception in zip(
            range(1, 2),
            [
                None
            ]
        )
    ],
    (
        Path("examples/example_py2yaml/python_files"),
        Path("examples/example_py2yaml/python_files/main.py"),
        Path("examples/example_py2yaml/yaml_files/script.yaml"),
        None
    )
]


@pytest.mark.parametrize(
    "project_root_dir,main_file,script,exception",
    py2yaml_params,
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


# @pytest.mark.parametrize(
#     "script,output_dir,exception,actor",
#
# )
# def test_yaml2py(script, output_dir, exception, actor, tmp_path):
#     def _test_yaml2py():
#         yaml2py(Path(script), tmp_path)
#         for file1, file2 in zip(o)
#     if exception:
#         with pytest.raises(exception):
#             _test_yaml2py()
#     else:
#         _test_yaml2py()
