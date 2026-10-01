"""Plain Python in bodies: what we need to write today."""

# mwe: int-today
from __future__ import annotations

from aiida_workgraph import task

from wishlist_types import Settings


@task
def seen(x: int) -> int:
    return x


def test_int_today(aiida_profile):
    @task.graph
    def inner(cfg: Settings) -> int:
        nspin = int(cfg.nspin)  # orm.Int -> int, or range() fails
        return seen(x=len(range(nspin))).result

    @task.graph
    def top(cfg: Settings) -> int:
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()
    assert graph.outputs.result.value == 2
# end mwe: int-today
