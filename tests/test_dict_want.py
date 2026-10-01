"""Eager and deferred bodies: what we would like to write."""

from __future__ import annotations

from typing import Annotated

import pytest
from aiida_workgraph import namespace, task


# mwe: dict-want
@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Dict for a dict input, and a graph body cannot return a plain value")
def test_dict_want(aiida_profile):
    @task.graph
    def inner(overrides: dict[str, int]) -> bool:
        return isinstance(overrides, dict)  # today: False once it runs, overrides arrives as an orm.Dict

    @task.graph
    def top(overrides: dict[str, int]) -> Annotated[dict, namespace(eager=bool, deferred=bool)]:
        return {
            "eager": isinstance(overrides, dict),  # today: True, a plain dict arrives here
            "deferred": inner(overrides=overrides).result,
        }

    graph = top.build(overrides={"ecutwfc": 40})  # today: TypeError: Invalid graph return payload, "eager" is a plain value
    graph.run()
    assert (graph.outputs.eager.value, graph.outputs.deferred.value) == (True, True)
# end mwe: dict-want
