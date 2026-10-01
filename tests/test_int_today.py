"""Plain Python in bodies: what we need to write today."""

from __future__ import annotations

from typing import Annotated

from aiida_workgraph import namespace, task

from wishlist_types import Settings


# mwe: int-today
@task
def as_output(x: int) -> int:  # a graph output must be a socket, so a body's value goes through a task
    return x


def test_int_today(aiida_profile):
    @task.graph
    def deferred_graph(cfg: Settings) -> int:
        nspin = int(cfg.nspin)  # orm.Int -> int, or range() fails
        return as_output(x=len(range(nspin))).result

    @task.graph
    def eager_graph(cfg: Settings) -> Annotated[dict, namespace(eager=int, deferred=int)]:
        return {
            "eager": as_output(x=len(range(cfg.nspin))).result,  # a plain int here; no coercion needed
            "deferred": deferred_graph(cfg=cfg).result,
        }

    graph = eager_graph.build(cfg=Settings(nspin=2))
    graph.run()
    assert (graph.outputs.eager.value, graph.outputs.deferred.value) == (2, 2)
# end mwe: int-today
