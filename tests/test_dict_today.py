"""Eager and deferred bodies: what we need to write today."""

# mwe: dict-today
from __future__ import annotations

from aiida_workgraph import task


@task
def seen(x: bool) -> bool:
    return x


def test_dict_today(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        overrides = dict(overrides)  # proxy over orm.Dict -> dict
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value
# end mwe: dict-today
