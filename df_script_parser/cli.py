from pathlib import Path
import argparse
from .tools import py2yaml, yaml2py


def is_dir(path: str) -> Path:
    path = Path(path)
    if path.is_dir():
        return path
    raise argparse.ArgumentTypeError(f"Not a dir: {path}")


def is_file(path: str) -> Path:
    path = Path(path)
    if path.is_file():
        return path
    raise argparse.ArgumentTypeError(f"Not a file: {path}")


def py2yaml_cli():
    parser = argparse.ArgumentParser(description=py2yaml.__doc__)
    parser.add_argument(
        "input_file",
        metavar="INPUT_FILE",
        help="Python script to parse.",
        type=is_file,
    )
    parser.add_argument(
        "output_dir",
        metavar="OUTPUT_DIR",
        help="Directory to store parser output in.",
        type=is_dir,
    )
    args = parser.parse_args()
    py2yaml(**vars(args))


def yaml2py_cli():
    parser = argparse.ArgumentParser(description=yaml2py.__doc__)
    parser.add_argument(
        "input_dir",
        metavar="INPUT_DIR",
        help="Directory with yaml files.",
        type=is_dir,
    )
    parser.add_argument(
        "output_file",
        metavar="OUTPUT_FILE",
        help="Python file, output.",
        type=is_file,
    )
    args = parser.parse_args()
    yaml2py(**vars(args))
