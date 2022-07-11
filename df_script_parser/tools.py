import typing as tp
from pathlib import Path
import libcst as cst
import logging
from .parse import Parser
from .processors import NodeProcessor, Disambiguator
from .dumpers_loaders import yaml_dumper_loader, pp
from black import format_file_in_place, FileMode, WriteBack


def py2yaml(
        input_file: tp.Union[str, Path],
        output_file: tp.Union[str, Path],
        safe_mode: bool = True,
) -> None:
    """Parse python script INPUT_FILE into import.yaml containing information about imports used in the script,
    script.yaml containing a dictionary found inside the file.
    If the file contains an instance of df_engine.Actor class its arguments will be parsed and special labels
    will be placed in script.yaml.

    All the files are stored in OUTPUT_DIR."""
    input_file = Path(input_file)
    output_file = Path(output_file)

    with open(input_file, "r") as f:
        parsed_file = cst.parse_module(f.read())

    logging.info(f"File {input_file} parsed")

    transformer = Parser(input_file.parent, safe_mode=safe_mode)

    parsed_file.visit(transformer)

    script = NodeProcessor(
        transformer.dicts[transformer.args.get("script") or "script"],
        list(transformer.imports),
        start_label=transformer.args.get("start_label"),
        fallback_label=transformer.args.get("fallback_label"),
        safe_mode=safe_mode,
    ).result

    with open(output_file, "w") as f:
        yaml_dumper_loader.dump(dict(imports=transformer.imports.get_dict(), script=script), f)


def yaml2py(
        input_file: tp.Union[str, Path],
        output_file: tp.Union[str, Path],
) -> None:
    """Generate a python script OUTPUT_FILE from import.yaml and script.yaml inside the INPUT_DIR.

    Generation rules:

    * If a string inside the `script.yaml` is a correct python code within the context of imports
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
    with open(output_file, "w") as output:
        # write imports
        with open(input_file, "r") as f:
            loaded_input_file = yaml_dumper_loader.load(f)
        loaded_imports = loaded_input_file["imports"]
        script = loaded_input_file["script"]
        imports = []
        for key in loaded_imports.keys():
            for module in loaded_imports[key].keys():
                for code in loaded_imports[key][module]:
                    imports.append(code)
        output.write("\n".join(imports) + "\n\n")

        disambiguation = Disambiguator(script, imports)
        output.write("\nscript = ")
        pp(disambiguation.result, output)
        output.write("\nstart_label = ")
        pp(
            tuple(disambiguation.start_label) if disambiguation.start_label else None,
            output,
        )
        output.write("\nfallback_label = ")
        pp(
            tuple(disambiguation.fallback_label) if disambiguation.fallback_label else None,
            output,
        )
        output.write("\n")
        output.write("from df_engine.core import Actor\n" "\nactor = Actor(script, start_label, fallback_label)\n")
    format_file_in_place(output_file, fast=False, mode=FileMode(), write_back=WriteBack.YES)
