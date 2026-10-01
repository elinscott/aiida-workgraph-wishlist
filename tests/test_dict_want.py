"""Eager and deferred bodies: what we would like to write."""

# mwe: dict-want
from __future__ import annotations

import pytest
from aiida_workgraph import task


@task
def seen(x: bool) -> bool:
    return x


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Dict for a dict input")
def test_dict_want(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value  # today: False, overrides is an orm.Dict here
# end mwe: dict-want
