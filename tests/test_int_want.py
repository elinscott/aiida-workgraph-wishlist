"""Plain Python in bodies: what we would like to write."""

# mwe: int-want
from __future__ import annotations

import pytest
from aiida_workgraph import task

from wishlist_types import Settings


@task
def seen(x: int) -> int:
    return x


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Int for an int field")
def test_int_want(aiida_profile):
    @task.graph
    def inner(cfg: Settings) -> int:
        return seen(x=len(range(cfg.nspin))).result

    @task.graph
    def top(cfg: Settings) -> int:
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()  # today: inner fails, TypeError: 'Int' object cannot be interpreted as an integer
    assert graph.outputs.result.value == 2
# end mwe: int-want
