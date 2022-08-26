"""This module contains a class that parses a file
"""
import logging
import typing as tp
from pathlib import Path

import libcst as cst
import libcst.matchers as m
from df_engine.core.actor import Actor

from df_script_parser.processors.dict_processors import NodeProcessor
from df_script_parser.utils.convenience_functions import evaluate
from df_script_parser.utils.exceptions import StarredError
from df_script_parser.utils.namespaces import Namespace

# Match nodes with Actor calls e.g. `a = Actor(args)` or `b = df_engine.core.Actor(args)`
actor_call_matcher = m.Call()

actor_matcher = m.OneOf(m.Assign(value=actor_call_matcher), m.AnnAssign(value=actor_call_matcher))


class Parser(m.MatcherDecoratableTransformer):
    """Class that parses python script files. Removes all the supported nodes

    :param project_root_dir: Root directory of the project
    :type project_root_dir: :py:class:`pathlib.Path`
    :param namespace: Namespace to store all the extracted objects in
    :type namespace: :py:class:`df_script_parser.utils.namespaces.Namespace`
    """

    def __init__(self, project_root_dir: Path, namespace: Namespace):
        super().__init__()
        self.project_root_dir: Path = Path(project_root_dir)
        self.namespace: Namespace = namespace
        self.node_processor: NodeProcessor = NodeProcessor(namespace)

    def add_assignment(
            self,
            add_function: tp.Callable[[str, ...], None],
            node: cst.Assign | cst.AnnAssign,
            *args
    ):
        """Process :py:class:`libcst.Assign` and :py:class:`libcst.AnnAssign`

        :param add_function: Function to call to add the assigned object to the namespace
        :type add_function:
            Callable[[str, Any], None]
        :param node: Node from which assignment targets are extracted
        :type node: :py:class:`libcst.Assign` | :py:class:`libcst.AnnAssign`
        :param args: Arguments to pass to the function
        :return: None
        """
        if isinstance(node, cst.AnnAssign):
            add_function(evaluate(node.target), *args)
        elif isinstance(node, cst.Assign):
            first_target = evaluate(node.targets[0].target)
            add_function(first_target, *args)
            for target in node.targets[1:]:
                self.namespace.add_alt_name(first_target, evaluate(target.target))
        else:
            raise ValueError(
                f"Parameter node should be of type libcst.Assign or libcst.AnnAssign, type of the node: {type(node)}."
            )

    @m.leave(m.OneOf(m.AnnAssign(value=m.Dict()), m.Assign(value=m.Dict())))
    def add_dict(
            self,
            original_node: cst.AnnAssign | cst.Assign,
            updated_node: cst.AnnAssign | cst.Assign
    ) -> cst.RemovalSentinel:
        """Adds a dictionary assignment to the namespace

        :param original_node: Original node
        :type original_node: :py:class:`libcst.AnnAssign` | :py:class:`libcst.Assign`
        :param updated_node: Also original node
        :type updated_node: :py:class:`libcst.AnnAssign` | :py:class:`libcst.Assign`
        :return: :py:class:`libcst.RemovalSentinel`
        """
        self.node_processor.parse_tuples = False
        self.add_assignment(
            self.namespace.add_dict,
            original_node,
            self.node_processor(cst.ensure_type(original_node.value, cst.Dict))
        )
        return cst.RemoveFromParent()

    @m.call_if_not_inside(m.Dict())
    @m.leave(actor_matcher)
    def parse_actor_args(
            self,
            original_node: tp.Union[cst.Assign, cst.AnnAssign],
            updated_node: tp.Union[cst.Assign, cst.AnnAssign]
    ) -> tp.Union[cst.RemovalSentinel, cst.Assign, cst.AnnAssign]:
        """Parse arguments of a call to :py:class:`df_engine.core.Actor`

        :param original_node:
        :param updated_node:
        :return:
        """
        func_name = evaluate(cst.ensure_type(original_node.value, cst.Call).func)
        if self.namespace.get_absolute_name(
                func_name
        ) in ["df_engine.core.actor.Actor", "df_engine.core.Actor"]:
            args = {}
            actor_arg_order = Actor.__init__.__wrapped__.__code__.co_varnames[1:]
            for arg, keyword in zip(cst.ensure_type(original_node.value, cst.Call).args, actor_arg_order):
                if arg.keyword is not None:
                    keyword = evaluate(arg.keyword)
                self.node_processor.parse_tuples = True
                args[keyword] = self.node_processor(arg.value)
                logging.info("Found actor call arg %s = %s", keyword, args[keyword])
            self.add_assignment(
                self.namespace.add_function_call,
                original_node,
                func_name,
                args,
                True
            )
            return cst.RemoveFromParent()
        return updated_node

    @m.leave(m.Import() | m.ImportFrom())
    def add_import_to_structure(self, node: tp.Union[cst.Import, cst.ImportFrom], *args) -> cst.RemovalSentinel:
        """Add an import to the namespace

        :param node:
        :param args:
        :return:
        """
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
