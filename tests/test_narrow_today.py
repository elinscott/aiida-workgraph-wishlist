"""Type narrowing: what we need to write today."""

from __future__ import annotations

import pytest
from aiida_workgraph import task

from wishlist_types import SpinType

# mwe: narrow-today
@task
def ph(spin: SpinType) -> str:
    return "ran ph.x"


def test_narrow_today(aiida_profile):
    @task.graph
    def eager_graph(spin: SpinType) -> str:
        spin = SpinType(spin.value)  # proxy over EnumData -> member
        if spin is SpinType.NON_COLLINEAR:  # the narrowing, by hand, in every graph that reaches ph.x
            raise NotImplementedError(f"spin={spin.value!r} cannot reach ph.x; use 'none' or 'collinear'")
        return ph(spin=spin.value).result  # member -> str before it crosses a socket

    graph = eager_graph.build(spin=SpinType.NONE)
    graph.run()
    assert graph.outputs.result.value == "ran ph.x"

    with pytest.raises(NotImplementedError):
        eager_graph.build(spin=SpinType.NON_COLLINEAR)
# end mwe: narrow-today
