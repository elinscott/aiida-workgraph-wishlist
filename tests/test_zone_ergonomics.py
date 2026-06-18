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
# WISH: the Map item should be ergonomic -- no `.value`, no unpack @task
# ----------------------------------------------------------------------


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: `Map.item` is the map_item task's OUTPUTS "
    "namespace (a `key` port and a `value` port), so user code must write "
    "`z.item.value` to get the item (and `z.item.key` for its key). Passing "
    "`z.item` directly raises 'link a top-level output socket without a parent'. "
    "We wish the item were usable directly -- `.value` is internal machinery a "
    "user should never have to type."
)
def test_map_item_usable_without_dot_value(collect):
    """WISH: ``z.item`` is the item, no ``.value`` ceremony."""

    @task
    def sink(item) -> dict:
        return {"_tag": "item_direct", "n": item["n"]}

    @task.graph
    def top():
        with Map(make_items()) as z:
            sink(item=z.item)  # wish: z.item IS the item, not its outputs namespace

    rs = collect(top, "item_direct")
    assert sorted(r["n"] for r in rs) == [7, 99]


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: a Map item is a future, so you cannot subscript "
    "it inline (`z.item.value['a']` raises). Destructuring an N-field item therefore "
    "forces a dedicated unpack @task with one named output per field (see "
    "aiida-koopmans2 `unpack_empty_item` / `unpack_block_item`) -- a per-iteration "
    "process node and boilerplate that should not be necessary. We wish item fields "
    "could feed a task directly."
)
def test_destructure_map_item_without_unpack_task(collect):
    """WISH: feed a Map item's fields into a task without a wrapper unpack @task."""

    @task
    def two_field_items() -> Annotated[dict, dynamic(dict)]:
        return {"k1": {"a": 1, "b": 2}, "k2": {"a": 10, "b": 20}}

    @task
    def sink(a, b) -> dict:
        return {"_tag": "destructure", "total": a + b}

    @task.graph
    def top():
        with Map(two_field_items()) as z:
            sink(a=z.item.value["a"], b=z.item.value["b"])

    rs = collect(top, "destructure")
    assert sorted(r["total"] for r in rs) == [3, 30]
