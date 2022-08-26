import typing as tp

from df_engine.core import Actor, Context
from df_engine.core.types import NodeLabel3Type


def greeting_flow_n2_transition(
        ctx: Context, actor: Actor, *args, **kwargs
) -> NodeLabel3Type:
    return "greeting_flow", "node2", 1.0


def high_priority_node_transition(
        flow_label: str, label: str
) -> tp.Callable[..., NodeLabel3Type]:
    def transition(ctx: Context, actor: Actor, *args, **kwargs) -> NodeLabel3Type:
        return flow_label, label, 2.0

    return transition
