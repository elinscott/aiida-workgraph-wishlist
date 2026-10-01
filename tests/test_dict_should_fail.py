"""Eager and deferred bodies: should start failing once the wish is granted."""

from __future__ import annotations

from aiida_workgraph import task


# mwe: dict-should-fail
@task
def as_output(x: bool) -> bool:  # a graph output must be a socket, so a body's value goes through a task
    return x


def test_dict_should_fail(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        return as_output(x=overrides.get_dict() == {"ecutwfc": 40}).result

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because overrides is a proxy over orm.Dict, which has .get_dict()
    # wanted: AttributeError: 'dict' object has no attribute 'get_dict'
# end mwe: dict-should-fail
