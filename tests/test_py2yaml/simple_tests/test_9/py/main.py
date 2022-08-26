from df_engine.core import keywords as kw
from df_engine.core.actor import Actor

another_script = script = {
    "flow": {
        "node": {
            kw.RESPONSE: "hi"
        }
    }
}

actor = Actor(
    script,
    ("flow", "node"),
)
