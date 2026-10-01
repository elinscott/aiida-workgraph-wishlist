"""Eager and deferred bodies: what we need to write today."""

# mwe: dict-today
from __future__ import annotations

from aiida_workgraph import task


@task
def as_output(x: bool) -> bool:  # a graph output must be a socket, so a body\'s value goes through a task
    return x


def test_dict_today(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        overrides = dict(overrides)  # proxy over orm.Dict -> dict
        return as_output(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value
# end mwe: dict-today
