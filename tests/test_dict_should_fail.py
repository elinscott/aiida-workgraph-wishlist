"""Eager and deferred bodies: should start failing once the wish is granted."""

# mwe: dict-should-fail
from __future__ import annotations

from aiida_workgraph import task


@task
def seen(x: bool) -> bool:
    return x


def test_dict_should_fail(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        return seen(x=overrides.get_dict() == {"ecutwfc": 40}).result

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because overrides is a proxy over orm.Dict, which has .get_dict()
    # wanted: AttributeError: 'dict' object has no attribute 'get_dict'
# end mwe: dict-should-fail
