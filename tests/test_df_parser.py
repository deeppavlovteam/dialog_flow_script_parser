"""Parser tests."""
from pathlib import Path

import pytest

from df_script_parser import py2yaml, yaml2py
from df_script_parser import __version__
from df_script_parser.utils.convenience_functions import get_module_name
from df_script_parser.utils.module_metadata import get_location


def test_version():
    assert __version__ == "0.1.0"


# class TestIntegration:
#     """Test all the components of the parser together."""
#     @pytest.mark.parametrize(
#         "input_file,output_file",
#         [(example / "py" / "main.py", example / "py2yaml" / "script.yaml") for example in Path("examples").iterdir()],
#     )
#     def test_py2yaml(self, input_file, output_file, tmp_path):
#         """Test the py2yaml part of the parser."""
#         py2yaml(input_file, Path(input_file).parent, tmp_path / "script.yaml")
#         with open(output_file, "r") as file_1, open(tmp_path / "script.yaml", "r") as file_2:
#             assert file_1.read() == file_2.read()
#
#     @pytest.mark.parametrize(
#         "input_file,output_file",
#         [(example / "py2yaml" / "script.yaml",
#           example / "yaml2py" / "main.py") for example in Path("examples").iterdir()],
#     )
#     def test_yaml2py(self, input_file, output_file, tmp_path):
#         """Test the yaml2py part of the parser."""
#         yaml2py(input_file, tmp_path / "main.py")
#         with open(output_file, "r") as file_1, open(tmp_path / "main.py", "r") as file_2:
#             assert file_1.read() == file_2.read()

class TestFunctions:
    @pytest.mark.parametrize(
        "file,project_root_dir,answer",
        [
            (
                Path("tests/test_directory/__init__.py"),
                Path("tests/test_directory/"),
                "test_directory"
            ),
            (
                Path("tests/test_directory/file.py"),
                Path("tests/test_directory/"),
                "test_directory.file"
            ),
            (
                Path("tests/test_directory/another_package/__init__.py"),
                Path("tests/test_directory/"),
                "test_directory.another_package"
            ),
            (
                Path("tests/test_directory/another_package/file.py"),
                Path("tests/test_directory/"),
                "test_directory.another_package.file"
            ),
            (
                Path("tests/test_directory/dir/file.py"),
                Path("tests/test_directory/dir"),
                "file"
            )
        ]
    )
    def test_get_module_name(self, file, project_root_dir, answer):
        assert get_module_name(file, project_root_dir) == answer

    @pytest.mark.parametrize(
        "module_name,directory,answer",
        [
            (
                "file",
                Path("tests/test_directory/"),
                Path("tests/test_directory/file.py").absolute(),
            ),
            (
                "file",
                Path("tests/test_directory/another_package"),
                Path("tests/test_directory/another_package/file.py").absolute(),
            ),
            (
                "another_package",
                Path("tests/test_directory/"),
                Path("tests/test_directory/another_package/__init__.py").absolute(),
            ),
            (
                "..file",
                Path("tests/test_directory/another_package"),
                Path("tests/test_directory/file.py").absolute(),
            ),
        ]
    )
    def test_get_location(self, module_name, directory, answer):
        assert Path(get_location(module_name, directory)).absolute() == answer
