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


def test_subscript_in_deferred_body_resolves(collect):
    """Subscripting a dict input inside a @task.graph body returns the value."""

    @task
    def sink(n) -> dict:
        return {"_tag": "subscript", "n": n}

    @task.graph
    def inner(block: dict):
        sink(n=block["n"])  # subscript on a TaggedValue -> concrete int

    @task.graph
    def top():
        inner(block=make_block().result)

    [r] = collect(top, "subscript")
    assert r["n"] == 7


def test_structural_branch_in_deferred_body(collect):
    """A real ``if`` on a subscripted value picks the right branch per invocation.

    Folklore says "never branch in a graph body"; in a *deferred* body it works.
    """

    @task
    def took_a() -> dict:
        return {"_tag": "branch", "branch": "a"}

    @task
    def took_b() -> dict:
        return {"_tag": "branch", "branch": "b"}

    @task.graph
    def inner(block: dict):
        if block["kind"] == Kind.A:
            took_a()
        else:
            took_b()

    @task.graph
    def top():
        inner(block=make_block().result)

    [r] = collect(top, "branch")
    assert r["branch"] == "a"


def test_is_none_works_in_deferred_body(collect):
    """``x is None`` DOES work for a None-valued input (None arrives unwrapped).

    Documented as a guard precisely because it is the surprising counterpart to
    the ``is <enum>`` footgun below.
    """

    @task
    def sink(is_none) -> dict:
        return {"_tag": "is_none", "is_none": is_none}

    @task.graph
    def inner(block: dict):
        sink(is_none=(block["opt"] is None))

    @task.graph
    def top():
        inner(block=make_block().result)

    [r] = collect(top, "is_none")
    assert r["is_none"] is True


# end mwe: deferred-body-values


def test_eq_against_enum_in_deferred_body(collect):
    """``==`` against an Enum member works (the proxy forwards ``__eq__``)."""

    @task
    def sink(eq) -> dict:
        return {"_tag": "eq", "eq": eq}

    @task.graph
    def inner(block: dict):
        sink(eq=(block["kind"] == Kind.A))

    @task.graph
    def top():
        inner(block=make_block().result)

    [r] = collect(top, "eq")
    assert r["eq"] is True


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
def test_is_against_enum_in_deferred_body(collect):
    """We wish ``block['kind'] is Kind.A`` were not silently False."""

    @task
    def sink(is_a) -> dict:
        return {"_tag": "is_enum", "is_a": is_a}

    @task.graph
    def inner(block: dict):
        # The wrapped value equals Kind.A (== is True), but the proxy is a
        # distinct object, so `is` is False.
        sink(is_a=(block["kind"] is Kind.A))

    @task.graph
    def top():
        inner(block=make_block().result)

    [r] = collect(top, "is_enum")
    assert r["is_a"] is True
