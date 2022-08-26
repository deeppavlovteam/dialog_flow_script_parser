from df_engine.core import keywords
from df_engine.core.actor import Actor

script = {
    "flow": {
        "node": {
            keywords.RESPONS: "hi"
        }
    }
}

actor = Actor(
    script,
    ("flow", "node"),
)
