"""``from __future__ import annotations`` and dynamic namespaces.

PEP 563 (the modern default in many codebases -- every aiida-koopmans2 module
uses it) stringises annotations. The engine reads a dynamic-namespace annotation
at runtime to build the per-item links; historically, as a string it could not
resolve, failing with ``name 'Annotated' is not defined`` mid-run. This whole
module carries the future import so that path is exercised.

GRANTED: aiida-workgraph #788 (closes #783) resolves the stringised annotation,
so a dynamic-namespace graph task now runs under PEP 563. Promoted from a wish
(``xfail``) to a guard.
"""

from __future__ import annotations

from typing import Annotated

from aiida_workgraph import dynamic, namespace, task


# mwe: future-annotations
def test_dynamic_namespace_works_under_future_annotations(aiida_profile):
    @task
    def src() -> Annotated[dict, namespace(data=dynamic(int))]:
        return {"data": {"k1": 1, "k2": 2}}

    @task
    def double(v):
        return 2 * v

    @task.graph
    def fan(data: Annotated[dict, dynamic(int)]) -> Annotated[dict, namespace(out=dynamic(int))]:
        return {"out": {key: double(v=value).result for key, value in data.items()}}

    @task.graph
    def top() -> Annotated[dict, namespace(out=dynamic(int))]:
        return {"out": fan(data=src().data).out}

    graph = top.build()
    graph.run()
    assert (graph.outputs.out.k1.value, graph.outputs.out.k2.value) == (2, 4)


# end mwe: future-annotations
