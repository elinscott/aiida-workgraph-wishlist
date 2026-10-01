"""How ``None`` survives (or doesn't) across socket boundaries.

This bit us for real: ``aiida-koopmans2/workgraphs/kcp.py`` deliberately models
its per-step inputs as a *frozen dataclass* rather than a ``TypedDict``, because
dataclass routing (``dataclasses.asdict`` -> ``cls(**value)``) preserves
``None`` fields, whereas exploding a dict/TypedDict into a namespace of sockets
drops the ``None``-valued leaves. Closed-shell tutorial_1
(``tot_magnetization=None``) hit exactly that.

The two cases below isolate the rule:

* a ``None`` passed as a *task input argument* (a namespace leaf) is silently
  dropped -> WISH (``xfail``);
* a ``None`` carried *inside an opaque dict value* round-trips fine -> PASS
  (the documented safe path / why the dataclass workaround works).
"""

from __future__ import annotations

import pytest
from aiida_workgraph import task


# mwe: none-kwarg
@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: passing None as a task input argument silently "
    "drops the socket -- the parameter falls back to its default (or errors with "
    "'missing argument' if there is none). We wish an explicit None were delivered "
    "as None, or rejected loudly at build time, rather than silently vanishing."
)
def test_none_task_input_is_delivered(aiida_profile):
    @task
    def sink(x="SENTINEL"):
        return x is None

    @task.graph
    def top():
        return sink(x=None).result  # silently dropped today -> x defaults to "SENTINEL"

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value


# end mwe: none-kwarg


def test_none_inside_opaque_dict_survives(aiida_profile):
    """``None`` carried inside a whole-dict value round-trips intact.

    This is the safe path (and why kcp.py's dataclass workaround works): keep the
    None inside an opaque payload rather than exposing it as its own socket.
    """

    @task
    def make() -> dict:
        return {"a": 1, "b": None, "c": "x"}

    @task
    def seen(x):
        return x

    @task.graph
    def inner(d: dict):
        return seen(x="b" in d and d.get("b") is None).result

    @task.graph
    def top():
        return inner(d=make().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value
