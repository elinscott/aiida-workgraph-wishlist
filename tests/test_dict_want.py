"""Eager and deferred bodies: what we would like to write."""

from __future__ import annotations

import pytest
from aiida_workgraph import task


# mwe: dict-want
@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Dict for a dict input, and a graph body cannot return a plain value")
def test_dict_want(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        # today: overrides arrives as an orm.Dict (a plain dict when top-level), so this is False
        return isinstance(overrides, dict)  # today: a graph body may not return a plain value

    @task.graph
    def top(overrides: dict[str, int]) -> bool:
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value  # today: None, inner failed
# end mwe: dict-want
