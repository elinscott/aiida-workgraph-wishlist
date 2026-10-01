"""Enums: should start failing once the wish is granted."""

# mwe: enum-should-fail
from __future__ import annotations

from aiida_workgraph import task

from wishlist_types import SpinType


@task
def as_output(x: bool) -> bool:  # a graph output must be a socket, so a body\'s value goes through a task
    return x


def test_enum_should_fail(aiida_profile):
    @task.graph
    def inner(spin: SpinType) -> bool:
        return as_output(x=spin.get_member() is SpinType.COLLINEAR).result

    @task.graph
    def top(spin: SpinType) -> bool:
        return inner(spin=spin).result

    graph = top.build(spin=SpinType.COLLINEAR)
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because spin is a proxy over orm.EnumData, which forwards .get_member()
    # wanted: AttributeError: 'SpinType' object has no attribute 'get_member'
# end mwe: enum-should-fail
