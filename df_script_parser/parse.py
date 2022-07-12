import libcst as cst
import typing as tp
import libcst.matchers as m
from .parse_utils import ImportBlock, evaluate
from pathlib import Path
import logging
from .processors import NodeProcessor
from df_engine.core.actor import Actor

# Match nodes with Actor calls e.g. `a = Actor(args)` or `b = df_engine.core.Actor(args)`
actor_call_matcher = m.Call(func=m.OneOf(m.Name("Actor"), m.Attribute(attr=m.Name("Actor"))))

actor_matcher = m.OneOf(m.Assign(value=actor_call_matcher), m.AnnAssign(value=actor_call_matcher))


class Parser(m.MatcherDecoratableVisitor):
    def __init__(self, path: tp.Union[str, Path], safe_mode: bool = True):
        super().__init__()
        self.path: tp.Union[str, Path] = path
        self.imports: ImportBlock = ImportBlock(working_dir=self.path)
        self.dicts: tp.Dict[str, cst.Dict] = {}
        self.args: tp.Dict[str, tp.Any] = {}
        self.safe_mode = safe_mode
        logging.debug(f"Created Parser with path={path}")

    @m.visit(m.AnnAssign(value=m.Dict()))
    def add_dict(self, node: cst.AnnAssign) -> None:
        self.dicts[evaluate(node.target)] = node.value

    @m.visit(m.Assign(value=m.Dict()))
    def add_dicts(self, node: cst.Assign) -> None:
        for target in node.targets:
            self.dicts[evaluate(target.target)] = node.value

    @m.call_if_not_inside(m.Dict())
    @m.visit(actor_matcher)
    def parse_actor_args(self, node: tp.Union[cst.Assign, cst.AnnAssign]) -> None:
        """Parse arguments of calls to df_engine.core.Actor. Store them in self.args."""
        actor_arg_order = Actor.__init__.__wrapped__.__code__.co_varnames[1:]
        node.value: cst.Call
        for arg, keyword in zip(node.value.args, actor_arg_order):
            if arg.keyword is not None:
                keyword = evaluate(arg.keyword)
            self.args[keyword] = NodeProcessor(
                arg.value, list(self.imports), parse_tuples=True, safe_mode=self.safe_mode
            ).result
            logging.info(f"Found arg {keyword} = {self.args[keyword]}")

    @m.visit(m.Import() | m.ImportFrom())
    def add_import_to_structure(self, node: tp.Union[cst.Import, cst.ImportFrom]) -> None:
        """Add import statement block to the self.structure."""
        self.imports.append(node)
