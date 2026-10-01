"""Enums: should start failing once the wish is granted."""

from __future__ import annotations

from aiida_workgraph import task

from wishlist_types import SpinType


# mwe: enum-should-fail
@task
def as_output(x: bool) -> bool:  # a graph output must be a socket, so a body's value goes through a task
    return x


def test_enum_should_fail(aiida_profile):
    @task.graph
    def deferred_graph(spin: SpinType) -> bool:
        return as_output(x=spin.get_member() is SpinType.COLLINEAR).result

    @task.graph
    def eager_graph(spin: SpinType) -> bool:
        return deferred_graph(spin=spin).result

    graph = eager_graph.build(spin=SpinType.COLLINEAR)
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because spin is a proxy over orm.EnumData, which forwards .get_member()
    # wanted: AttributeError: 'SpinType' object has no attribute 'get_member'
# end mwe: enum-should-fail
