import typing as tp
from pathlib import Path
import logging

import libcst.matchers as m
import libcst as cst
from df_engine.core.actor import Actor

from df_script_parser.processors.dict_processors import NodeProcessor
from df_script_parser.utils.exceptions import WrongFileStructure, StarredError
from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.namespaces import Namespace


# Match nodes with Actor calls e.g. `a = Actor(args)` or `b = df_engine.core.Actor(args)`
actor_call_matcher = m.Call()

actor_matcher = m.OneOf(m.Assign(value=actor_call_matcher), m.AnnAssign(value=actor_call_matcher))


class Parser(m.MatcherDecoratableTransformer):
    def __init__(self, project_root_dir: Path, namespace: Namespace):
        super().__init__()
        self.project_root_dir: Path = Path(project_root_dir)
        self.namespace: Namespace = namespace
        self.args: tp.Dict[str, tp.Any] = {}
        self.node_processor: NodeProcessor = NodeProcessor(namespace)

    @m.leave(m.AnnAssign(value=m.Dict()))
    def add_dict(self, node: cst.AnnAssign, *args) -> cst.RemovalSentinel:
        self.node_processor.parse_tuples = False
        self.namespace.add_dict(evaluate(node.target), self.node_processor(cst.ensure_type(node.value, cst.Dict)))
        return cst.RemoveFromParent()

    @m.leave(m.Assign(value=m.Dict()))
    def add_dicts(self, node: cst.Assign, *args) -> cst.RemovalSentinel:
        self.node_processor.parse_tuples = False
        first_target = evaluate(node.targets[0].target)
        self.namespace.add_dict(first_target, self.node_processor(node.value))
        for target in node.targets[1:]:
            self.namespace.add_alt_name(first_target, evaluate(target.target))
        return cst.RemoveFromParent()

    @m.call_if_not_inside(m.Dict())
    @m.leave(actor_matcher)
    def parse_actor_args(
            self,
            original_node: tp.Union[cst.Assign, cst.AnnAssign],
            updated_node: tp.Union[cst.Assign, cst.AnnAssign]
    ) -> tp.Union[cst.RemovalSentinel, cst.Assign, cst.AnnAssign]:
        """Parse arguments of calls to df_engine.core.Actor. Store them in self.args."""
        if self.namespace.get_absolute_name(
                evaluate(cst.ensure_type(original_node.value, cst.Call).func)
        ) in ["df_engine.core.actor.Actor", "df_engine.core.Actor"]:
            if self.args:
                raise WrongFileStructure("Only one Actor call is allowed.")
            actor_arg_order = Actor.__init__.__wrapped__.__code__.co_varnames[1:]
            for arg, keyword in zip(cst.ensure_type(original_node.value, cst.Call).args, actor_arg_order):
                if arg.keyword is not None:
                    keyword = evaluate(arg.keyword)
                self.node_processor.parse_tuples = True
                self.args[keyword] = self.node_processor(arg.value)
                logging.info(f"Found arg {keyword} = {self.args[keyword]}")
            return cst.RemoveFromParent()
        return updated_node

    @m.leave(m.Import() | m.ImportFrom())
    def add_import_to_structure(self, node: tp.Union[cst.Import, cst.ImportFrom], *args) -> cst.RemovalSentinel:
        """Add import statement block to the self.structure."""
        if isinstance(node, cst.Import):
            for name in node.names:
                self.namespace.add_import(name.evaluated_name, name.evaluated_alias)
        elif isinstance(node, cst.ImportFrom):
            if isinstance(node.names, cst.ImportStar):
                raise StarredError(f"ImportStar is not allowed: {evaluate(node)}")
            module_name = len(node.relative) * "." + evaluate(node.module or "")
            for name in node.names:
                self.namespace.add_from_import(module_name, name.evaluated_name, name.evaluated_alias)
        return cst.RemoveFromParent()
