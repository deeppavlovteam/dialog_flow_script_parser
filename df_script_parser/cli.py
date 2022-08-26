# from pathlib import Path
# import argparse
# from df_script_parser.tools import py2yaml, yaml2py
#
#
# def is_file(arg: str) -> Path:
#     path = Path(arg)
#     if path.is_file():
#         return path
#     raise argparse.ArgumentTypeError(f"Not a file: {path}")
#
#
# def py2yaml_cli():
#     parser = argparse.ArgumentParser(description=py2yaml.__doc__)
#     parser.add_argument(
#         "input_file",
#         metavar="INPUT_FILE",
#         help="Python script to parse.",
#         type=is_file,
#     )
#     parser.add_argument(
#         "output_file",
#         metavar="OUTPUT_FILE",
#         help="Yaml file to store parser output in.",
#         type=str,
#     )
#     args = parser.parse_args()
#     py2yaml(**vars(args))
#
#
# def yaml2py_cli():
#     parser = argparse.ArgumentParser(description=yaml2py.__doc__)
#     parser.add_argument(
#         "input_file",
#         metavar="INPUT_FILE",
#         help="Yaml file to load.",
#         type=is_file,
#     )
#     parser.add_argument(
#         "output_file",
#         metavar="OUTPUT_FILE",
#         help="Python file, output.",
#         type=str,
#     )
#     args = parser.parse_args()
#     yaml2py(**vars(args))
