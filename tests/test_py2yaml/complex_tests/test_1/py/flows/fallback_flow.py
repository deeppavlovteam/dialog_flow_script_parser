from ..nodes import start_node as sn
from ..nodes.fallback_node import fallback_node

fallback_flow = {
    "fallback_node": fallback_node,
    "other_node": sn.start_node
}
