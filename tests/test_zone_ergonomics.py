"""Operations on raw *future* sockets (``TaskSocket``) outside a deferred body.

On a raw ``task.outputs`` socket / ``z.value`` in a zone body, your value is a
``TaskSocket`` (a future). Empirically (aiida-workgraph 0.9.0, upstream main @
502c1b5b; node-graph 0.6.5) the framework treats different operations very
differently:

* **arithmetic** (``socket * 2``, ``socket // 2``) is *supported* -- it builds a
  deferred operator task (``op_mul`` / ``op_floordiv``). So the team folklore
  "never do socket arithmetic" is, for these operators, unnecessary -> PASS.
* **subscript** (``socket["k"]``) raises ``GraphDeferredIllegalOperationError``
  -- a good, loud error, but it forces a wrapper ``@task`` for the very common
  "index a Map item" case -> the WISH (``xfail``).

The asymmetry (arithmetic builds an op task, subscript refuses) is itself worth
raising with the devs.

GRANTED since the first version of this module: aiida-workgraph #792 (closes
#785) replaced the ``z.item`` outputs namespace with ``z.value`` and ``z.key``,
so the item no longer arrives as internal machinery the user has to reach
through. ``z.item`` survives as a deprecated alias. Promoted to a guard below.
"""

from typing import Annotated

import pytest
from aiida_workgraph import Map, dynamic, namespace, task

# NOTE: deliberately NO ``from __future__ import annotations`` here -- the dynamic
# fan-out task needs its ``Annotated[dict, dynamic(dict)]`` hint resolved to a
# real object at runtime (the engine reads it to build the namespace links);
# stringised annotations break that with "name 'Annotated' is not defined".


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
            sink(n=z.value["n"])  # subscript of a future

    with pytest.raises(GraphDeferredIllegalOperationError):
        top.build()


def test_map_value_is_the_item(collect):
    """GUARD: ``z.value`` is the current entry, ``z.key`` its key.

    Was a wish (#785): the zone used to expose ``z.item``, the map_item task's
    OUTPUTS namespace, so user code had to write ``z.item.value`` -- internal
    machinery a user should never type -- and passing ``z.item`` itself raised
    "link a top-level output socket without a parent". #792 granted it.
    ``z.item`` still resolves, with a DeprecationWarning.
    """

    @task
    def sink(item, key) -> dict:
        return {"_tag": "map_value", "n": item["n"], "key": str(key)}

    @task.graph
    def top():
        with Map(make_items()) as z:
            sink(item=z.value, key=z.key)

    rs = collect(top, "map_value")
    assert sorted((r["key"], r["n"]) for r in rs) == [("i1", 7), ("i2", 99)]


# ----------------------------------------------------------------------
# The documented dynamic fan-out (no Map zone) -- this is the clean way
# ----------------------------------------------------------------------


def test_dynamic_fanout_via_for_loop_is_clean(collect):
    """The docs' scatter-gather: ``for k, v in data.items()`` in a ``@task.graph``.

    No ``Map`` zone, no unpack ``@task``. The body is deferred, so ``data`` is
    concrete: you iterate it and subscript each item inline. This is the
    documented dynamic fan-out and the clean answer to the Map wish below --
    aiida-koopmans2's Map zones (`unpack_block_item` etc.) are the anti-pattern.
    """

    @task
    def items() -> Annotated[dict, namespace(data=dynamic(dict))]:
        return {"data": {"k1": {"a": 1, "b": 2}, "k2": {"a": 10, "b": 20}}}

    @task
    def combine(a, b) -> dict:
        return {"_tag": "fanout", "total": int(a) + int(b)}

    @task.graph
    def fan(data: Annotated[dict, dynamic(dict)]):
        for _key, item in data.items():
            combine(a=item["a"], b=item["b"])  # subscript inline; no unpack task

    @task.graph
    def top():
        fan(data=items().data)

    rs = collect(top, "fanout")
    assert sorted(r["total"] for r in rs) == [3, 30]


# ----------------------------------------------------------------------
# WISH: destructuring a Map item should not need an unpack @task
# ----------------------------------------------------------------------


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: a Map entry "
    "is a future, so it cannot be subscripted inline -- `z.value['a']` raises "
    "GraphDeferredIllegalOperationError. Destructuring an N-field item therefore "
    "forces a dedicated unpack @task with one named output per field (see "
    "aiida-koopmans2 `unpack_empty_item` / `unpack_block_item`) -- a per-iteration "
    "process node and boilerplate that should not be necessary. Arithmetic on the "
    "same future builds an operator task, so the refusal is an asymmetry, not a "
    "limit (scinode/node-graph #156, PR #160). (Documented escape hatch: "
    "`for k, v in data.items()` in a @task.graph subscripts inline -- see the guard "
    "above; the Map zone is the anti-pattern.)"
)
def test_destructure_map_item_without_unpack_task(collect):
    """WISH: feed a Map entry's fields into a task without a wrapper unpack @task."""

    @task
    def two_field_items() -> Annotated[dict, dynamic(dict)]:
        return {"k1": {"a": 1, "b": 2}, "k2": {"a": 10, "b": 20}}

    @task
    def sink(a, b) -> dict:
        return {"_tag": "destructure", "total": a + b}

    @task.graph
    def top():
        with Map(two_field_items()) as z:
            sink(a=z.value["a"], b=z.value["b"])

    rs = collect(top, "destructure")
    assert sorted(r["total"] for r in rs) == [3, 30]
