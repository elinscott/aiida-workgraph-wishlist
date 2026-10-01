"""Plain Python in bodies: what we would like to write."""

from __future__ import annotations

import pytest
from aiida_workgraph import task

from wishlist_types import Settings


# mwe: int-want
@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Int for an int field, and a graph body cannot return a plain value")
def test_int_want(aiida_profile):
    @task.graph
    def inner(cfg: Settings) -> int:
        # today: cfg.nspin arrives as an orm.Int (a plain int when top-level), so range() raises TypeError
        return len(range(cfg.nspin))  # today: a graph body may not return a plain value

    @task.graph
    def top(cfg: Settings) -> int:
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()  # today: inner fails, TypeError: 'Int' object cannot be interpreted as an integer
    assert graph.outputs.result.value == 2  # today: None, inner failed
# end mwe: int-want
