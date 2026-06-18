"""``from __future__ import annotations`` breaks dynamic namespaces.

PEP 563 (the modern default in many codebases -- every aiida-koopmans2 module
uses it) stringises annotations. The engine reads a dynamic-namespace annotation
at runtime to build the per-item links; as a string it can't resolve, failing
with ``name 'Annotated' is not defined`` mid-run. This whole module carries the
future import so the failure reproduces.
"""

from __future__ import annotations

from typing import Annotated

import pytest
from aiida_workgraph import dynamic, namespace, task


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: with `from __future__ import annotations`, a "
    "dynamic-namespace hint is a string the engine cannot resolve at runtime "
    "('name Annotated is not defined'). Dropping the future import fixes it, but "
    "PEP 563 is the modern default -- we wish stringised annotations were supported."
)
def test_dynamic_namespace_works_under_future_annotations(collect):
    @task
    def src() -> Annotated[dict, namespace(data=dynamic(int))]:
        return {"data": {"k1": 1, "k2": 2}}

    @task
    def sink(v) -> dict:
        return {"_tag": "future", "v": int(v)}

    @task.graph
    def fan(data: Annotated[dict, dynamic(int)]):
        for _key, value in data.items():
            sink(v=value)

    @task.graph
    def top():
        fan(data=src().data)

    rs = collect(top, "future")
    assert sorted(r["v"] for r in rs) == [1, 2]
