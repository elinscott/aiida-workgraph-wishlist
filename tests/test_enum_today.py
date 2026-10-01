"""Enums: what we need to write today."""

from __future__ import annotations

from aiida_workgraph import task

from wishlist_types import SpinType


# mwe: enum-today
@task
def classify(spin: SpinType) -> str:
    spin = SpinType(spin)  # a task body receives the bare str
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"


def test_enum_today(aiida_profile):
    @task.graph
    def eager_graph(spin: SpinType) -> str:
        spin = SpinType(spin.value)  # proxy over EnumData -> member
        return classify(spin=spin.value).result  # member -> str before it crosses a socket

    graph = eager_graph.build(spin=SpinType.COLLINEAR)  # crosses only because pyproject registers an aiida.data entry point for SpinType
    graph.run()
    assert graph.outputs.result.value == "polarized"
# end mwe: enum-today
