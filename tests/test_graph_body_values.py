"""What a *deferred* ``@task.graph`` body actually sees.

When a ``@task.graph`` is invoked as a node (not the top-level definition), its
body runs at *runtime* via ``node_graph.utils.graph.materialize_graph``, which
hands the body its inputs as ``TaggedValue`` proxies wrapping the concrete,
resolved values. Empirically (aiida-workgraph 0.8.1):

* subscript, ``==`` (incl. against an Enum), structural branching, and even
  ``is None`` all see the real per-invocation value -> PASS (regression guards);
* ``is`` against a non-None object (e.g. an Enum member) is the one silent
  footgun -> WISH (``xfail``).

That ``is None`` works but ``is <enum>`` does not is the key subtlety: None
arrives unwrapped, but other values arrive as a ``wrapt.ObjectProxy`` whose
identity is the proxy's, not the wrapped object's.
"""

from __future__ import annotations

from enum import Enum

import pytest
from aiida_workgraph import task


# ----------------------------------------------------------------------
# These WORK today (regression guards)
# ----------------------------------------------------------------------


# mwe: deferred-body-values
class Kind(str, Enum):
    A = "a"
    B = "b"


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
        if block["kind"] == Kind.A:
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


def test_eq_against_enum_in_deferred_body(aiida_profile):
    """``==`` against an Enum member works (the proxy forwards ``__eq__``)."""

    @task.graph
    def inner(block: dict):
        return seen(x=block["kind"] == Kind.A).result

    @task.graph
    def top():
        return inner(block=make_block().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value


# ----------------------------------------------------------------------
# WISH: ``is`` against a non-None object is silently wrong
# ----------------------------------------------------------------------


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: a non-None graph input arrives as a wrapt "
    "ObjectProxy (TaggedValue); `value is EnumMember` compares the proxy's "
    "identity, not the wrapped value, so it is silently False. `==` works; only "
    "`is` is affected. We wish `is` either matched the wrapped value or refused "
    "to compile (it cannot be detected at runtime)."
)
def test_is_against_enum_in_deferred_body(aiida_profile):
    """We wish ``block['kind'] is Kind.A`` were not silently False."""

    @task.graph
    def inner(block: dict):
        # The wrapped value equals Kind.A (== is True), but the proxy is a
        # distinct object, so `is` is False.
        return seen(x=block["kind"] is Kind.A).result

    @task.graph
    def top():
        return inner(block=make_block().result).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value
