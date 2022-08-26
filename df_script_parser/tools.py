from pathlib import Path

from black import format_file_in_place, FileMode, WriteBack

from df_script_parser.dumpers_loaders import yaml_dumper_loader
from df_script_parser.processors.dict_processors import Disambiguator
from df_script_parser.processors.recursive_parser import RecursiveParser
from df_script_parser.utils.namespaces import Import, From, Call


def py2yaml(
        root_file: Path,
        project_root_dir: Path,
        output_file: Path,
):
    with open(Path(output_file).absolute(), "w") as outfile:
        yaml_dumper_loader.dump(
            RecursiveParser(Path(project_root_dir).absolute()).parse_project_dir(
                Path(root_file).absolute()
            ),
            outfile
        )


def yaml2py(
        yaml_file: Path,
        extract_to_directory: Path,
):
    """Extract project from a yaml file to a directory

    :param yaml_file: Yaml file to extract from
    :type yaml_file: :py:class:`.Path`
    :param extract_to_directory: Directory to extract to
    :type extract_to_directory: :py:class:`.Path`
    :return: None
    """
    with open(Path(yaml_file).absolute(), "r") as infile:
        processed_file = yaml_dumper_loader.load(infile)
    namespaces = processed_file.get("namespaces")
    if not namespaces:
        raise RuntimeError("No namespaces found")
    for namespace in namespaces:
        path = namespace.split(".")
        path_to_file = Path(extract_to_directory).absolute().joinpath(*path[:-1])
        if not path_to_file.exists():
            path_to_file.mkdir(parents=True, exist_ok=True)
        path_to_file = path_to_file / (str(path[-1]) + ".py")
        # if path_to_file.exists():
        #     raise RuntimeError(f"File {path_to_file} already exists")
        with open(path_to_file, "w") as outfile:
            disambiguator = Disambiguator()
            for name, value in namespaces[namespace].items():
                if isinstance(value, (Import, From)):
                    outfile.write(repr(value) + f" as {name}\n")
                elif isinstance(value, Call):
                    disambiguator.replace_lists_with_tuples = True
                    for arg in value.args:
                        value.args[arg] = disambiguator(value.args[arg])
                    outfile.write(f"{name} = {repr(value)}\n")
                    disambiguator.replace_lists_with_tuples = False
                else:
                    disambiguator.replace_lists_with_tuples = False
                    outfile.write(f"{name} = {disambiguator(value)}\n")
                disambiguator.add_name(name)
        format_file_in_place(path_to_file, fast=False, mode=FileMode(), write_back=WriteBack.YES)
