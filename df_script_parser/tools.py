import typing as tp
from pathlib import Path
import libcst as cst
from .parse import Parser
from .processors import NodeProcessor, Disambiguator
from .dumpers_loaders import yaml_dumper_loader
from black import FileMode, format_str
from io import StringIO


def py2yaml_str(
    py_contents: str,
    working_dir: tp.Union[str, Path],
    safe_mode: bool = True,
) -> str:
    """Py2yaml but takes file contents as str and returns str."""
    parsed_file = cst.parse_module(py_contents)

    transformer = Parser(working_dir, safe_mode=safe_mode)

    parsed_file.visit(transformer)

    script = NodeProcessor(
        transformer.dicts[transformer.args.get("script") or "script"],
        list(transformer.imports),
        start_label=transformer.args.get("start_label"),
        fallback_label=transformer.args.get("fallback_label"),
        safe_mode=safe_mode,
    ).result

    buffer = StringIO()
    yaml_dumper_loader.dump(dict(imports=transformer.imports.get_dict(), script=script), buffer)

    return buffer.getvalue()


def py2yaml(
    input_file: tp.Union[str, Path],
    output_file: tp.Union[str, Path],
    safe_mode: bool = True,
) -> None:
    """Parse python script INPUT_FILE into OUTPUT_FILE containing information about imports used in the script,
    and a dictionary found inside the file.
    If the INPUT_FILE contains an instance of df_engine.Actor class its arguments will be parsed and special tags
    will be placed in OUTPUT_FILE."""
    input_file = Path(input_file)
    output_file = Path(output_file)

    with open(input_file, "r") as input_f:
        with open(output_file, "w") as output_f:
            output_f.write(py2yaml_str(input_f.read(), input_file.parent, safe_mode))


def yaml2py_str(
    yaml_contents: str,
) -> str:
    """Yaml2py but takes yaml contents as str and returns a string."""
    loaded_input_file = yaml_dumper_loader.load(yaml_contents)

    loaded_imports = loaded_input_file["imports"]
    script = loaded_input_file["script"]

    imports = []
    for key in loaded_imports.keys():
        for module in loaded_imports[key].keys():
            for code in loaded_imports[key][module]:
                imports.append(code)

    disambiguation = Disambiguator(script, imports)
    return format_str(
        "\n".join(
            [
                *imports,
                "",
                "",
                f"script = {disambiguation.result}",
                "",
                f"start_label = {tuple(disambiguation.start_label) if disambiguation.start_label else None}",
                "",
                f"fallback_label = {tuple(disambiguation.fallback_label) if disambiguation.fallback_label else None}",
                "",
                "from df_engine.core import Actor",
                "",
                "actor = Actor(script, start_label, fallback_label)",
            ]
        ),
        mode=FileMode(),
    )


def yaml2py(
    input_file: tp.Union[str, Path],
    output_file: tp.Union[str, Path],
) -> None:
    """Generate a python script OUTPUT_FILE from yaml INPUT_FILE.

    Generation rules:

    * If a string inside the dictionary of INPUT_FILE is a correct python code within the context of imports
        it will be displayed in the OUTPUT_FILE without quotations.
        If you want to specify how the string should be displayed
        use !str tag for strings and !py tag for lines of code.
    * If a {dictionary {key / value} / list value} has a !start or !start:str or !start:py tag
        the path to that element will be stored in a start_label variable.
    * If a {dictionary {key / value} / list value} has a tag !fallback or !fallback:str or !fallback:py tag
        the path to that key will be stored in a fallback_label variable.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    with open(input_file, "r") as input_f:
        with open(output_file, "w") as output_f:
            output_f.write(yaml2py_str(input_f.read()))
