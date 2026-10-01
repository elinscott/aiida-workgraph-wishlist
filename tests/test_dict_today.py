"""Eager and deferred bodies: what we need to write today."""

from __future__ import annotations

from typing import Annotated

from aiida_workgraph import namespace, task


# mwe: dict-today
@task
def as_output(x: bool) -> bool:  # a graph output must be a socket, so a body's value goes through a task
    return x


def test_dict_today(aiida_profile):
    @task.graph
    def deferred_graph(overrides: dict[str, int]) -> bool:
        overrides = dict(overrides)  # proxy over orm.Dict -> dict
        return as_output(x=isinstance(overrides, dict)).result

    @task.graph
    def eager_graph(overrides: dict[str, int]) -> Annotated[dict, namespace(eager=bool, deferred=bool)]:
        return {
            "eager": as_output(x=isinstance(overrides, dict)).result,  # a plain dict here; no coercion needed
            "deferred": deferred_graph(overrides=overrides).result,
        }

    graph = eager_graph.build(overrides={"ecutwfc": 40})
    graph.run()
    assert (graph.outputs.eager.value, graph.outputs.deferred.value) == (True, True)
# end mwe: dict-today
