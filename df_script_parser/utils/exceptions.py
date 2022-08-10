"""Exceptions for the parser."""


class ParserError(Exception):
    """Raised during parsing."""


class WrongFileStructure(ParserError):  # ToDo: rewrite doc, add file formats md
    """Class for exceptions raised due to invalid file structure.
    For more on correct file structure see `file_formats.md`."""


class StarredError(ParserError):  # ToDo: rewrite doc
    """Class for exceptions raised due to using star notation which is not supported by the parser."""


class ModuleNotFoundParserError(ParserError):
    """Raised when a module imported in a file being parsed is not found."""


class ResolutionError(ParserError):
    """Raised when a :func:`df_script_parser.utils.namespaces.Namespace.resolve` method cannot resolve an expression."""


class ObjectNotFound(ResolutionError):
    """Raised when the resolve method cannot locate an object inside the namespace."""


class NamespaceNotParsed(ResolutionError):
    """Raised when a namespace which a request is referencing is not available for parsing.
    This could happen due to :class:`WrongFileStructure` or :class:`ModuleNotFoundParserError`."""


class KeyNotFound(ResolutionError):
    """Raised when a :class:`KeyError` would be raised."""


class RequestParsingError(ResolutionError):
    """Raised when name_resolution_parser cannot parse a request due to it not being of the right format."""
