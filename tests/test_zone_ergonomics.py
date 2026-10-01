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


# ----------------------------------------------------------------------
# These WORK today (regression guards)
# ----------------------------------------------------------------------


# mwe: map-value
@task
def make_items() -> Annotated[dict, dynamic(dict)]:
    return {"i1": {"n": 7}, "i2": {"n": 99}}


def test_map_value_is_the_item(aiida_profile):
    @task
    def sink(item, key):
        return f"{key}={item['n']}"

    @task.graph
    def top() -> Annotated[dict, namespace(seen=dynamic(str))]:
        with Map(make_items()) as z:
            z.gather({"seen": sink(item=z.value, key=z.key).result})
        return {"seen": z.outputs.seen}

    graph = top.build()
    graph.run()
    assert (graph.outputs.seen.i1.value, graph.outputs.seen.i2.value) == ("i1=7", "i2=99")


# end mwe: map-value


def test_socket_arithmetic_builds_operator_tasks(aiida_profile):
    """``socket * 2`` and ``socket // 2`` work -- node-graph builds operator tasks."""

    @task
    def make_n() -> int:
        return 21

    @task.graph
    def top() -> Annotated[dict, namespace(mul=int, floordiv=int)]:
        n = make_n().result
        return {"mul": n * 2, "floordiv": n // 2}

    graph = top.build()
    graph.run()
    assert (graph.outputs.mul.value, graph.outputs.floordiv.value) == (42, 10)


def test_eager_subscript_of_future_raises_loudly():
    """Subscripting a future in a zone body raises a clear, specific error.

    Documents the current (good, loud) behaviour so a regression is visible.
    """
    from node_graph.errors import GraphDeferredIllegalOperationError

    @task
    def sink(n):
        return n

    @task.graph
    def top():
        with Map(make_items()) as z:
            sink(n=z.value["n"])  # subscript of a future

    with pytest.raises(GraphDeferredIllegalOperationError):
        top.build()


# ----------------------------------------------------------------------
# The documented dynamic fan-out (no Map zone) -- this is the clean way
# ----------------------------------------------------------------------


# mwe: for-loop-fanout
def test_dynamic_fanout_via_for_loop_is_clean(aiida_profile):
    @task
    def items() -> Annotated[dict, namespace(data=dynamic(dict))]:
        return {"data": {"k1": {"a": 1, "b": 2}, "k2": {"a": 10, "b": 20}}}

    @task
    def combine(a, b):
        return int(a) + int(b)

    @task.graph
    def fan(data: Annotated[dict, dynamic(dict)]) -> Annotated[dict, namespace(totals=dynamic(int))]:
        # subscript inline; no unpack task
        return {"totals": {key: combine(a=item["a"], b=item["b"]).result for key, item in data.items()}}

    @task.graph
    def top() -> Annotated[dict, namespace(totals=dynamic(int))]:
        return {"totals": fan(data=items().data).totals}

    graph = top.build()
    graph.run()
    assert (graph.outputs.totals.k1.value, graph.outputs.totals.k2.value) == (3, 30)


# end mwe: for-loop-fanout


# ----------------------------------------------------------------------
# WISH: destructuring a Map item should not need an unpack @task
# ----------------------------------------------------------------------


# mwe: map-destructure
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
def test_destructure_map_item_without_unpack_task(aiida_profile):
    @task
    def two_field_items() -> Annotated[dict, dynamic(dict)]:
        return {"k1": {"a": 1, "b": 2}, "k2": {"a": 10, "b": 20}}

    @task
    def add(a, b):
        return a + b

    @task.graph
    def top() -> Annotated[dict, namespace(totals=dynamic(int))]:
        with Map(two_field_items()) as z:
            z.gather({"totals": add(a=z.value["a"], b=z.value["b"]).result})
        return {"totals": z.outputs.totals}

    graph = top.build()
    graph.run()
    assert (graph.outputs.totals.k1.value, graph.outputs.totals.k2.value) == (3, 30)


# end mwe: map-destructure
