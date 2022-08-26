from df_engine.core import keywords
from df_engine.core.actor import Actor

script = {
    keywords.GLOBAL: {
        keywords.RESPONSE: ""
    }
}

actor = Actor(
    script,
    (keywords.GLOBAL, keywords.RESPONSE),
)
