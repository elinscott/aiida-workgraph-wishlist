"""Plain Python in bodies: what we would like to write."""

from __future__ import annotations

from typing import Annotated

import pytest
from aiida_workgraph import namespace, task

from wishlist_types import Settings


# mwe: int-want
@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Int for an int field, and a graph body cannot return a plain value")
def test_int_want(aiida_profile):
    @task.graph
    def deferred_graph(cfg: Settings) -> int:
        return len(range(cfg.nspin))  # today: TypeError once it runs, cfg.nspin arrives as an orm.Int

    @task.graph
    def eager_graph(cfg: Settings) -> Annotated[dict, namespace(eager=int, deferred=int)]:
        return {
            "eager": len(range(cfg.nspin)),  # today: 2, a plain int arrives here
            "deferred": deferred_graph(cfg=cfg).result,
        }

    graph = eager_graph.build(cfg=Settings(nspin=2))  # today: TypeError: Invalid graph return payload, "eager" is a plain value
    graph.run()
    assert (graph.outputs.eager.value, graph.outputs.deferred.value) == (2, 2)
# end mwe: int-want
