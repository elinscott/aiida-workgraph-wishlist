"""Operations on raw *future* sockets (``TaskSocket``) outside a deferred body.

On a raw ``task.outputs`` socket / ``z.item.value`` in a zone body, your value is
a ``TaskSocket`` (a future). Empirically (aiida-workgraph 0.8.1) the framework
treats different operations very differently:

* **arithmetic** (``socket * 2``, ``socket // 2``) is *supported* -- it builds a
  deferred operator task (``op_mul`` / ``op_floordiv``). So the team folklore
  "never do socket arithmetic" is, for these operators, unnecessary -> PASS.
* **subscript** (``socket["k"]``) raises ``GraphDeferredIllegalOperationError``
  -- a good, loud error, but it forces a wrapper ``@task`` for the very common
  "index a Map item" case -> the WISH (``xfail``).

The asymmetry (arithmetic builds an op task, subscript refuses) is itself worth
raising with the devs.
"""

from __future__ import annotations

from typing import Annotated

import pytest
from aiida_workgraph import Map, dynamic, task


@task
def make_items() -> Annotated[dict, dynamic(dict)]:
    return {"i1": {"n": 7}, "i2": {"n": 99}}


# ----------------------------------------------------------------------
# These WORK today (regression guards)
# ----------------------------------------------------------------------


def test_socket_arithmetic_builds_operator_tasks(collect):
    """``socket * 2`` and ``socket // 2`` work -- node-graph builds operator tasks."""

    @task
    def make_n() -> int:
        return 21

    @task
    def sink(mul, floordiv) -> dict:
        return {"_tag": "arith", "mul": mul, "floordiv": floordiv}

    @task.graph
    def top():
        n = make_n().result
        sink(mul=n * 2, floordiv=n // 2)

    [r] = collect(top, "arith")
    assert (r["mul"], r["floordiv"]) == (42, 10)


def test_eager_subscript_of_future_raises_loudly():
    """Subscripting a future in a zone body raises a clear, specific error.

    Documents the current (good, loud) behaviour so a regression is visible.
    """
    from node_graph.errors import GraphDeferredIllegalOperationError

    @task
    def sink(n) -> dict:
        return {"_tag": "loud", "n": n}

    @task.graph
    def top():
        with Map(make_items()) as z:
            sink(n=z.item.value["n"])  # subscript of a future

    with pytest.raises(GraphDeferredIllegalOperationError):
        top.build()


# ----------------------------------------------------------------------
# WISH: index a Map item inline without a wrapper @task
# ----------------------------------------------------------------------


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: subscripting a TaskSocket in a zone body raises "
    "GraphDeferredIllegalOperationError, so indexing a Map item requires a wrapper "
    "@task (or a nested @task.graph where the value is concrete). We wish "
    "`z.item.value['n']` worked inline -- especially given `socket * 2` already "
    "does."
)
def test_inline_subscript_of_map_item_should_work(collect):
    """WISH: index a Map item inline in the zone body."""

    @task
    def sink(n) -> dict:
        return {"_tag": "inline_subscript", "n": n}

    @task.graph
    def top():
        with Map(make_items()) as z:
            sink(n=z.item.value["n"])

    rs = collect(top, "inline_subscript")
    assert sorted(r["n"] for r in rs) == [7, 99]
