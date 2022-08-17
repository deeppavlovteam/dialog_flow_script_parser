"""Parser tests."""
from pathlib import Path

import pytest

from df_script_parser import __version__
from df_script_parser.utils.convenience_functions import get_module_name
from df_script_parser.utils.module_metadata import get_module_info, ModuleType
from df_script_parser.utils.exceptions import ModuleNotFoundParserError
from df_script_parser.utils.namespaces import Namespace


def test_version():
    assert __version__ == "0.1.0"


class TestSimpleFunctions:
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
        "args,answer,exception",
        [
            (
                ("file", Path("tests/test_directory/")),
                (ModuleType.LOCAL, str(Path("tests/test_directory/file.py").absolute())),
                None,
            ),
            (
                ("file", Path("tests/test_directory/another_package")),
                (ModuleType.LOCAL, str(Path("tests/test_directory/another_package/file.py").absolute())),
                None,
            ),
            (
                ("another_package", Path("tests/test_directory/")),
                (ModuleType.LOCAL, str(Path("tests/test_directory/another_package/__init__.py").absolute())),
                None,
            ),
            (
                ("..file", Path("tests/test_directory/another_package")),
                (ModuleType.LOCAL, str(Path("tests/test_directory/file.py").absolute())),
                None,
            ),
            (
                ("dir.file", Path("tests/test_directory")),
                (ModuleType.LOCAL, str(Path("tests/test_directory/dir/file.py").absolute())),
                None,
            ),
            (
                ("dir.file_does_not_exist", Path("tests/test_directory")),
                None,
                ModuleNotFoundParserError,
            ),
            (
                ("importlib.util", Path(".")),
                (ModuleType.SYSTEM, "importlib"),
                None,
            ),
            (
                ("importlib.does_not_exist", Path(".")),
                None,
                ModuleNotFoundParserError,
            ),
            (
                ("dff", Path(".")),
                (ModuleType.PIP,
                 "git+https://github.com/deepmipt/dialog_flow_engine.git@3a2e3e5d99cd3090c8f72315885dc91d398f2d74"),
                None,
            ),
            (
                ("df_engine.core.actor", Path(".")),
                (ModuleType.PIP, "df-engine==0.9.0"),
                None,
            ),
            (
                ("df_engine.core.actor_does_not_exist", Path(".")),
                None,
                ModuleNotFoundParserError,
            ),
            (
                ("package_does_not_exist", Path(".")),
                None,
                ModuleNotFoundParserError,
            ),
            (
                ("..nodes", Path("tests/test_py2yaml/complex_tests/test_1/py/flows")),
                (
                    ModuleType.LOCAL,
                    str(Path("tests/test_py2yaml/complex_tests/test_1/py/nodes/__init__.py").absolute())
                ),
                None
            ),
            (
                ("..nodes.fallback_node", Path("tests/test_py2yaml/complex_tests/test_1/py/flows")),
                (
                    ModuleType.LOCAL,
                    str(Path("tests/test_py2yaml/complex_tests/test_1/py/nodes/fallback_node.py").absolute())
                ),
                None
            ),
            (
                ("..main", Path("tests/test_py2yaml/complex_tests/test_1/py/flows")),
                (ModuleType.LOCAL, str(Path("tests/test_py2yaml/complex_tests/test_1/py/main.py").absolute())),
                None
            ),
        ]
    )
    def test_get_module_info(self, args, answer, exception):
        if exception:
            with pytest.raises(exception):
                get_module_info(*args)
        else:
            assert get_module_info(*args) == answer
#
# class TestNamespaceFunctions:
#     @pytest.fixture
#     def namespace(self):
#         space = Namespace(
#             Path("examples/example_py2yaml/py/main.py"),
#             Path("examples/example_py2yaml/py"),
#
#         )
