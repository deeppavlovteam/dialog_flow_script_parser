from df_script_parser import __version__
import pytest
from pathlib import Path
from df_script_parser import py2yaml, yaml2py


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.parametrize(
    "input_file,output_file",
    [(example / "py" / "main.py", example / "py2yaml" / "script.yaml") for example in Path("examples").iterdir()],
)
def test_py2yaml(input_file, output_file, tmp_path):
    py2yaml(input_file, tmp_path / "script.yaml")
    with open(output_file, "r") as file_1, open(tmp_path / "script.yaml", "r") as file_2:
        assert file_1.read() == file_2.read()


@pytest.mark.parametrize(
    "input_file,output_file",
    [(example / "py2yaml" / "script.yaml", example / "yaml2py" / "main.py") for example in Path("examples").iterdir()],
)
def test_yaml2py(input_file, output_file, tmp_path):
    yaml2py(input_file, tmp_path / "main.py")
    with open(output_file, "r") as file_1, open(tmp_path / "main.py", "r") as file_2:
        assert file_1.read() == file_2.read()
