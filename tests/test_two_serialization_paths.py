"""The serialization you can test is not the serialization that runs.

The obvious way to test that a graph will survive being handed to the engine is
``WorkGraph.from_dict(wg.to_dict())`` -- it is what aiida-koopmans2's shared
``assert_graph_roundtrips`` fixture does for every graph shape in the package.
Empirically (aiida-workgraph 0.9.0, upstream main @ 502c1b5b; node-graph 0.6.5)
that check is weaker than it looks:

* ``to_dict()`` is not serialization. It returns a dict of LIVE Python objects
  -- the graph input you passed comes back as the very same object, and the
  whole structure is not JSON-encodable -> PASS (the mechanism);
* so a graph can round-trip perfectly and still fail the moment it runs, on the
  values the round-trip handed back untouched -> WISH.

There is a third path this module cannot reach: the daemon persists
``task_inputs`` to the database on launch and rebuilds them in
``WorkGraphEngine.setup`` via ``restore_workgraph_data_from_raw_inputs``. An
in-process ``run()`` reaches that function with the live inputs, so the database
encode/decode never happens. A typed dynamic namespace on a task INPUT
(``datasets: Annotated[dict, dynamic(SnapshotDataset)]``) killed a live
workflow there with ``ValueError: Namespace structures do not match for
linking: ... Missing in source: []. Missing in target: []`` -- both lists empty,
because the check that failed was namespace-vs-leaf on a child the message
cannot name -- while ``from_dict(to_dict())`` on that exact graph succeeded.
That failure is NOT reproduced here; the reproduction recipe and its grading
are in ``proposed-issues/14-aiida-workgraph-two-serialization-paths.md``.

Two wishes: one serialization path a test can exercise, and an error message
that names the child that mismatched.
"""

import json
from enum import Enum
from typing import Annotated, TypedDict

import pytest
from aiida import orm
from aiida_workgraph import WorkGraph, dynamic, namespace, task


class SpinType(Enum):
    COLLINEAR = "collinear"


class Dataset(TypedDict):
    x: int
    y: int


@task
def extract(seed: int) -> Annotated[dict, namespace(x=int, y=int)]:
    return {"x": seed, "y": seed * 2}


@task
def train(datasets: Annotated[dict, dynamic(Dataset)]) -> dict:
    return {"_tag": "train", "n": len(dict(datasets))}


def test_to_dict_returns_live_objects(aiida_profile):
    """GUARD: ``to_dict()`` is a dict of live objects, not a serialized form.

    The mechanism behind the wish below: the input comes back as the identical
    object, and the structure as a whole is not JSON-encodable, so a
    ``from_dict(to_dict())`` round-trip never exercises any encoder the engine
    will use.
    """

    @task
    def leaf(spin) -> dict:
        return {"_tag": "live", "seen": str(spin)}

    @task.graph
    def top(spin: SpinType):
        leaf(spin=spin)

    data = top.build(spin=SpinType.COLLINEAR).to_dict()
    assert data["tasks"]["graph_inputs"]["inputs"]["spin"] is SpinType.COLLINEAR
    with pytest.raises(TypeError):
        json.dumps(data)


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a graph whose input the engine "
    "cannot serialize round-trips through `from_dict(to_dict())` without complaint, "
    "because `to_dict()` hands the object straight back, and then dies at run with "
    "`ValueError: Cannot serialize the provided object`. The round-trip is the check "
    "a test can make; it is not the check that decides whether the graph runs. We "
    "wish one serialization path were testable, or that a supported 'what the engine "
    "will do' check existed. (No escape hatch: the only honest test is a full run.)"
)
def test_a_graph_that_round_trips_also_runs(aiida_profile):
    """WISH: passing the round-trip means the graph will start."""

    @task
    def leaf(spin) -> dict:
        return {"_tag": "rt_then_run", "seen": str(spin)}

    @task.graph
    def top(spin: SpinType):
        leaf(spin=spin)

    graph = top.build(spin=SpinType.COLLINEAR)
    WorkGraph.from_dict(graph.to_dict())  # the guard every graph shape gets
    graph.run()  # ValueError: Cannot serialize the provided object


def test_typed_dynamic_namespace_round_trips_and_runs(aiida_profile):
    """GUARD: the shape that died on the daemon passes both in-process checks.

    Pinned as the negative control for the daemon-only failure described in the
    module docstring: on this version the fan-out into a TypedDict-typed
    dynamic input namespace both round-trips and runs, so an in-process suite
    has nothing to catch.
    """

    @task.graph
    def top(seed: int):
        datasets = {f"snap_{i}": extract(seed=seed + i) for i in range(2)}
        train(datasets=datasets)

    graph = top.build(seed=1)
    WorkGraph.from_dict(graph.to_dict())
    graph.run()

    [result] = [
        node.get_dict()
        for (node,) in orm.QueryBuilder().append(orm.Dict).all()
        if node.get_dict().get("_tag") == "train"
    ]
    assert result["n"] == 2
