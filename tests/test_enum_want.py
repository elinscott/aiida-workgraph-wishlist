"""Enums: what we would like to write."""

from __future__ import annotations

import pytest
from aiida_workgraph import task

from wishlist_types import SpinType


# mwe: enum-want
@task
def classify(spin: SpinType) -> str:
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"  # today: spin arrives as the str 'collinear', so this is False


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a task body receives an Enum member as its str")
def test_enum_want(aiida_profile):
    @task.graph
    def eager_graph(spin: SpinType) -> str:
        return classify(spin=spin).result  # today: spin is a proxy over an EnumData here

    graph = eager_graph.build(spin=SpinType.COLLINEAR)
    graph.run()  # today: ValueError: Cannot serialize the provided object, unless an aiida.data entry point names SpinType
    assert graph.outputs.result.value == "polarized"  # today: "unpolarized", the task body received the str 'collinear'
# end mwe: enum-want
