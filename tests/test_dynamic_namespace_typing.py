"""Dynamic-namespace *output* typing surprises (scatter-gather over namespaces).

The docs' scatter-gather only ever gathers *scalars* (`dynamic(int)`). Our real
fan-outs gather multi-field *namespaces* (e.g. BlockWannierize -> 3 files), and
there the typing matters in ways the docs don't cover:

* an explicit ``dynamic(namespace(...))`` output IS downstream-consumable (guard);
* the same shape declared through a ``TypedDict`` RETURN annotation is NOT --
  its dynamic field becomes an opaque ``workgraph.dict`` a namespace consumer
  can't link to, while ``dynamic(SomeTypedDict)`` inside an explicit
  ``namespace(...)`` return links fine (WISH);
* a gathered namespace re-scatters when it is passed to another ``@task.graph``,
  whose body iterates it deferred; iterating the future inline in the body that
  gathered it raises ``TaskSocketNamespace ... has no sub-socket 'items'`` (guard).

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


def test_explicit_namespace_gather_is_consumable(aiida_profile):
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
    def consume(out: Annotated[dict, dynamic(namespace(a=int))]) -> int:
        return sum(int(v["a"]) for v in out.values())

    @task.graph
    def top():
        return consume(out=fan(data=numbers().data).out).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == 3


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
def test_typeddict_return_annotation_is_consumable(aiida_profile):
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
    def consume(out: Annotated[dict, dynamic(Item)]) -> int:
        return sum(int(v["a"]) for v in out.values())

    @task.graph
    def top():
        return consume(out=fan(data=numbers().data).out).result

    graph = top.build()  # today: TypeError: Namespace item type mismatch: fan.out [workgraph.dict] -> consume.out [workgraph.namespace]
    graph.run()
    assert graph.outputs.result.value == 3


# end mwe: typeddict-return


# ----------------------------------------------------------------------
# Guard: a gathered namespace re-scatters through a nested @task.graph
# ----------------------------------------------------------------------


# mwe: rescatter
def test_gather_then_rescatter(aiida_profile):
    @task
    def scalars() -> Annotated[dict, namespace(data=dynamic(int))]:
        return {"data": {"k1": 1, "k2": 2}}

    @task
    def dbl(v) -> int:
        return int(v) * 2

    @task.graph
    def fan(data: Annotated[dict, dynamic(int)]) -> Annotated[dict, namespace(out=dynamic(int))]:
        return {"out": {key: dbl(v=value).result for key, value in data.items()}}

    @task.graph
    def top() -> Annotated[dict, namespace(out=dynamic(int))]:
        gathered = fan(data=scalars().data).out
        # re-scatter: hand the gathered namespace to a graph whose body iterates
        # it deferred; `gathered.items()` here, on the future, raises instead
        return {"out": fan(data=gathered).out}

    graph = top.build()
    graph.run()
    assert (graph.outputs.out.k1.value, graph.outputs.out.k2.value) == (4, 8)


# end mwe: rescatter
