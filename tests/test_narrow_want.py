"""Type narrowing: what we would like to write."""

from __future__ import annotations

from typing import Literal

import pytest
from aiida_workgraph import task

from wishlist_types import SpinType

# mwe: narrow-want
@task
def ph(spin: Literal[SpinType.NONE, SpinType.COLLINEAR]) -> str:
    return "ran ph.x"


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: a SpinType -> Literal[SpinType...] link is refused at build, and from an untyped source the Literal is not checked at all")
def test_narrow_want(aiida_profile):
    @task.graph
    def eager_graph(spin: SpinType) -> str:
        return ph(spin=spin).result  # SpinType -> Literal[...] link: allowed, checked where the value is known

    graph = eager_graph.build(spin=SpinType.NONE)  # today: TypeError: Socket annotated type mismatch, SpinType -> Literal is not allowed
    graph.run()
    assert graph.outputs.result.value == "ran ph.x"

    with pytest.raises(ValueError):  # the member is known at build, so the build refuses it
        eager_graph.build(spin=SpinType.NON_COLLINEAR)  # today, from an untyped source: DID NOT RAISE, and ph.x runs on a regime it cannot handle
# end mwe: narrow-want
