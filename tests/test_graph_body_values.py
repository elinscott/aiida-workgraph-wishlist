"""What a *deferred* ``@task.graph`` body actually sees.

When a ``@task.graph`` is invoked as a node (not the top-level definition), its
body runs at *runtime* and receives its inputs as ``TaggedValue`` proxies.
Empirically (aiida-workgraph 0.9.0, upstream main @ 502c1b5b; node-graph 0.6.5)
a ``dict`` input is a proxy over ``orm.Dict``, and subscripting it returns plain
Python values (an ``int``, a ``str``, ``None``). So subscript, a structural
``if`` on a subscripted value, and ``is None`` all see the real per-invocation
value -> PASS (regression guards).

An Enum member does not survive this way: see ``test_enum_coercion.py``
(``enum-graph-body``) for a member that arrives as a proxy, where ``==`` is True
and ``is`` is False.
"""

from __future__ import annotations

from aiida_workgraph import task


# ----------------------------------------------------------------------
# These WORK today (regression guards)
# ----------------------------------------------------------------------


# mwe: deferred-body-values
@task
def make_block() -> dict:
    return {"n": 7, "kind": "a", "opt": None}


@task
def seen(x):
    return x


def test_subscript_in_deferred_body_resolves(aiida_profile):
    @task.graph
    def inner(block: dict):
        return seen(x=block["n"]).result

    @task.graph
    def top():
        return inner(block=make_block().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == 7


def test_structural_branch_in_deferred_body(aiida_profile):
    @task
    def took_a():
        return "a"

    @task
    def took_b():
        return "b"

    @task.graph
    def inner(block: dict):
        if block["kind"] == "a":
            return took_a().result
        return took_b().result

    @task.graph
    def top():
        return inner(block=make_block().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == "a"


def test_is_none_works_in_deferred_body(aiida_profile):
    @task.graph
    def inner(block: dict):
        return seen(x=block["opt"] is None).result

    @task.graph
    def top():
        return inner(block=make_block().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value


# end mwe: deferred-body-values
