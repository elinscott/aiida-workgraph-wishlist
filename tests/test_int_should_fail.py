"""Plain Python in bodies: should start failing once the wish is granted."""

# mwe: int-should-fail
from __future__ import annotations

from aiida_workgraph import task

from wishlist_types import Settings


@task
def as_output(x: int) -> int:  # a graph output must be a socket, so a body\'s value goes through a task
    return x


def test_int_should_fail(aiida_profile):
    @task.graph
    def inner(cfg: Settings) -> int:
        return as_output(x=cfg.nspin.value).result

    @task.graph
    def top(cfg: Settings) -> int:
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()
    assert graph.outputs.result.value == 2
    # today: passes, because cfg.nspin is a proxy over orm.Int, which has .value
    # wanted: AttributeError: 'int' object has no attribute 'value'
# end mwe: int-should-fail
