"""Dynamic-namespace *output* typing surprises (scatter-gather over namespaces).

The docs' scatter-gather only ever gathers *scalars* (`dynamic(int)`). Our real
fan-outs gather multi-field *namespaces* (e.g. BlockWannierize -> 3 files), and
there the typing matters in ways the docs don't cover:

* an explicit ``dynamic(namespace(...))`` output IS downstream-consumable (guard);
* the same shape typed with a ``TypedDict`` (``dynamic(SomeTypedDict)``) is NOT
  -- it becomes an opaque ``workgraph.dict`` a namespace consumer can't link to
  (WISH);
* a gathered namespace can be consumed by a single downstream task, but it cannot
  be *re-scattered* (iterated in another ``@task.graph`` loop) (WISH).

This is *why* aiida-koopmans2's Map zones used ``gather()`` -- it explicitly
builds namespace output specs; the for-loop form needs explicit
``dynamic(namespace(...))`` typing to match.
"""

from typing import Annotated, TypedDict

import pytest
from aiida_workgraph import dynamic, namespace, task


# ----------------------------------------------------------------------
# Guard: explicit dynamic(namespace(...)) gather IS consumable downstream;
# WISH: a TypedDict-typed dynamic output should be equally consumable
# ----------------------------------------------------------------------


# mwe: typeddict-return
@task
def numbers() -> Annotated[dict, namespace(data=dynamic(dict))]:
    return {"data": {"k1": {"a": 1}, "k2": {"a": 2}}}


@task
def ident(x) -> int:
    # a graph task must return task OUTPUT SOCKETS, not raw values, so item
    # fields are routed through this passthrough before being assembled.
    return int(x)


def test_explicit_namespace_gather_is_consumable(collect):
    @task.graph
    def one(item) -> Annotated[dict, namespace(a=int)]:
        return {"a": ident(x=item["a"]).result}

    @task.graph
    def fan(
        data: Annotated[dict, dynamic(dict)],
    ) -> Annotated[dict, namespace(out=dynamic(namespace(a=int)))]:
        out = {}
        for key, item in data.items():
            out[key] = one(item=item)
        return {"out": out}

    @task
    def consume(out: Annotated[dict, dynamic(namespace(a=int))]) -> dict:
        return {"_tag": "explicit_ns", "total": sum(int(v["a"]) for v in out.values())}

    @task.graph
    def top():
        consume(out=fan(data=numbers().data).out)

    [r] = collect(top, "explicit_ns")
    assert r["total"] == 3


class Item(TypedDict):
    a: int


class Bundle(TypedDict):
    # a TypedDict used as a @task.graph RETURN annotation -- exactly the shape
    # of aiida-koopmans2's BlockWannierizeOutputs (-> a TypedDict whose field is
    # a dynamic namespace).
    out: Annotated[dict, dynamic(Item)]


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: a TypedDict used as a @task.graph RETURN "
    "annotation does not build a consumable namespace output -- the dynamic field "
    "becomes an opaque `workgraph.dict`, so a downstream namespace consumer fails to "
    "link ('Namespace item type mismatch: ... dict -> ... namespace'). An explicit "
    "`-> Annotated[dict, namespace(out=dynamic(Item))]` return annotation works "
    "(`dynamic(TypedDict)` as a *field* is fine; it is TypedDict-as-return that "
    "breaks). We wish TypedDict returns were at parity -- they are the project's "
    "standard data-shape type."
)
def test_typeddict_return_annotation_is_consumable(collect):
    @task.graph
    def one(item) -> Item:
        return Item(a=ident(x=item["a"]).result)

    @task.graph
    def fan(data: Annotated[dict, dynamic(dict)]) -> Bundle:  # TypedDict RETURN annotation
        out = {}
        for key, item in data.items():
            out[key] = one(item=item)
        return Bundle(out=out)

    @task
    def consume(out: Annotated[dict, dynamic(Item)]) -> dict:
        return {"_tag": "td_ret", "total": sum(int(v["a"]) for v in out.values())}

    @task.graph
    def top():
        consume(out=fan(data=numbers().data).out)

    [r] = collect(top, "td_ret")
    assert r["total"] == 3


# end mwe: typeddict-return


# ----------------------------------------------------------------------
# WISH: a gathered namespace should be re-scatterable, not just single-consumed
# ----------------------------------------------------------------------



# mwe: rescatter
@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: a gathered dynamic-namespace OUTPUT can be fed to "
    "one downstream task, but iterating it in another @task.graph "
    "(`for k, v in gathered.items()`) fails ('TaskSocketNamespace has no sub-socket'). "
    "We wish gather -> re-scatter worked, so a fan-out's results can fan out again."
)
def test_gather_then_rescatter(collect):
    @task
    def dbl(v) -> int:
        return int(v) * 2

    @task.graph
    def fan(data: Annotated[dict, dynamic(int)]) -> Annotated[dict, namespace(out=dynamic(int))]:
        out = {}
        for key, value in data.items():
            out[key] = dbl(v=value).result
        return {"out": out}

    @task
    def rec(v) -> dict:
        return {"_tag": "rescatter", "v": int(v)}

    @task
    def scalars() -> Annotated[dict, namespace(data=dynamic(int))]:
        return {"data": {"k1": 1, "k2": 2}}

    @task.graph
    def top():
        gathered = fan(data=scalars().data).out
        for _key, value in gathered.items():  # re-scatter the gathered namespace
            rec(v=value)

    rs = collect(top, "rescatter")
    assert sorted(r["v"] for r in rs) == [2, 4]


# end mwe: rescatter
