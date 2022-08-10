from pathlib import Path
import shutil
from df_script_parser.tools import py2yaml, yaml2py
import logging

logging.basicConfig(
    level=logging.WARNING,
    filename="build.log",
    filemode="w",
    format="%(levelname)s:%(filename)s:%(funcName)s:%(message)s",
)

examples = Path("examples")

for example in examples.iterdir():
    shutil.rmtree(example / "py2yaml") if (example / "py2yaml").exists() else None
    (example / "py2yaml").mkdir()
    py2yaml(example / "py" / "main.py", example / "py", example / "py2yaml" / "script.yaml")
    shutil.rmtree(example / "yaml2py") if (example / "yaml2py").exists() else None
    (example / "yaml2py").mkdir()
    yaml2py(example / "py2yaml" / "script.yaml", example / "yaml2py" / "main.py")
