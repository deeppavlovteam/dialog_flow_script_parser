import typing as tp
import re
from df_engine.core.keywords import (
    TRANSITIONS,
    RESPONSE,
    PROCESSING,
    GLOBAL,
    MISC,
    LOCAL as lcl,
)
import df_engine.conditions as cnd
import df_engine.labels as lbl
from df_engine.core import Actor, Context
import df_engine.responses as rsp
import dff
from functions import add_prefix
import transitions
from flow import global_flow
import flow


script = {
    GLOBAL: {
        TRANSITIONS: {
            ("greeting_flow", "node1", 1.1): cnd.regexp(r"\b(hi|hello)\b", re.I),
            ("music_flow", "node1", 1.1): cnd.regexp(r"talk about music"),
            lbl.to_fallback(0.1): cnd.true(),
            lbl.forward(): cnd.all(
                [
                    cnd.regexp(r"next\b"),
                    cnd.has_last_labels(
                        labels=[("music_flow", i) for i in ["node2", "node3"]]
                    ),
                ]
            ),
            lbl.repeat(0.2): cnd.all(
                [
                    cnd.regexp(r"repeat", re.I),
                    cnd.negation(cnd.has_last_labels(flow_labels=["global_flow"])),
                ]
            ),
        },
        PROCESSING: {1: add_prefix("l1_global"), 2: add_prefix("l2_global")},
        MISC: {"var1": "global_data", "var2": "global_data", "var3": "global_data"},
        RESPONSE: "",
    },
    "global_flow": global_flow,
    "greeting_flow": {
        "node1": {
            RESPONSE: rsp.choice(["Hi, what is up?", "Hello, how are you?"]),
            TRANSITIONS: {
                ("global_flow", "fallback_node", 0.1): cnd.true(),
                "node2": cnd.regexp(r"how are you"),
            },
            MISC: {"var3": "info_of_step_1"},
        },
        "node2": {
            RESPONSE: "Good. What do you want to talk about?",
            TRANSITIONS: {
                lbl.to_fallback(0.1): cnd.true(),
                lbl.forward(0.5): cnd.regexp(r"talk about"),
                ("music_flow", "node1"): cnd.regexp(r"talk about music"),
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
            },
        },
        "node3": {RESPONSE: "foo", TRANSITIONS: {lbl.forward(): cnd.regexp(r"bye")}},
        "node4": {
            RESPONSE: 'bar("bye")',
            TRANSITIONS: {
                "node1": cnd.regexp(r"hi|hello", re.IGNORECASE),
                lbl.to_fallback(): cnd.true(),
            },
        },
    },
    "music_flow": {
        "node1": {
            RESPONSE: "I love `System of a Down` group, would you like to tell about it? ",
            TRANSITIONS: {
                lbl.forward(): cnd.regexp(r"yes|yep|ok", re.IGNORECASE),
                lbl.to_fallback(): cnd.true(),
            },
        },
        "node2": {
            RESPONSE: "System of a Downis an Armenian-American heavy metal band formed in in 1994.",
            TRANSITIONS: {
                lbl.forward(): cnd.regexp(r"next", re.IGNORECASE),
                lbl.repeat(): cnd.regexp(r"repeat", re.IGNORECASE),
                lbl.to_fallback(): cnd.true(),
            },
        },
        "node3": {
            RESPONSE: "The band achieved commercial success with the release of five studio albums.",
            TRANSITIONS: {
                lbl.forward(): cnd.regexp(r"next", re.IGNORECASE),
                lbl.backward(): cnd.regexp(r"back", re.IGNORECASE),
                lbl.repeat(): cnd.regexp(r"repeat", re.IGNORECASE),
                lbl.to_fallback(): cnd.true(),
            },
        },
        "node4": {
            RESPONSE: "That's all what I know",
            TRANSITIONS: {
                transitions.greeting_flow_n2_transition: cnd.regexp(
                    r"next", re.IGNORECASE
                ),
                transitions.high_priority_node_transition(
                    "greeting_flow", "node4"
                ): cnd.regexp(r"next time", re.IGNORECASE),
                lbl.to_fallback(): cnd.true(),
            },
        },
    },
}

start_label = None

fallback_label = None

from df_engine.core import Actor

actor = Actor(script, start_label, fallback_label)
