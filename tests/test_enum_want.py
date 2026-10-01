"""Enums: what we would like to write."""

# mwe: enum-want
from __future__ import annotations

import pytest
from aiida_workgraph import task

from wishlist_types import SpinType


@task
def classify(spin: SpinType) -> str:
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a task body receives an Enum member as its str")
def test_enum_want(aiida_profile):
    @task.graph
    def top(spin: SpinType) -> str:
        return classify(spin=spin).result

    graph = top.build(spin=SpinType.COLLINEAR)
    graph.run()
    assert graph.outputs.result.value == "polarized"  # today: "unpolarized", the task body received the str 'collinear'
# end mwe: enum-want
