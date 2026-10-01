"""The serialization you can test is not the serialization that runs.

The obvious way to test that a graph will survive being handed to the engine is
``WorkGraph.from_dict(wg.to_dict())`` -- it is what aiida-koopmans2's shared
``assert_graph_roundtrips`` fixture does for every graph shape in the package.
Empirically (aiida-workgraph 0.9.0, upstream main @ 502c1b5b; node-graph 0.6.5)
that check is weaker than it looks:

* ``to_dict()`` is not serialization. It returns a dict of LIVE Python objects
  -- the graph input you passed comes back as the very same object, so the dict
  is JSON-encodable only when every input already is -> PASS (the mechanism);
* so a graph can round-trip perfectly and still fail the moment it runs, on the
  values the round-trip handed back untouched. ``run()`` serializes through
  ``to_engine_inputs()`` (``to_dict(should_serialize=True)``), a public method
  upstream's how-to documents, and calling it directly raises the same error at
  build, with no run -> PASS (the check to use instead of the round-trip).

There is a third path, the one the daemon takes: ``submit()`` saves a plumpy
checkpoint bundle and a worker unbundles it and steps the process, so the
inputs go through ``aiida.orm.utils.serialize`` rather than arriving live.
That path CAN be driven without a daemon, and the last guard below does it --
but nothing documents the recipe, and it is assembled from four private-ish
pieces (``instantiate_process``, ``AiiDAPersister``, ``get_object_loader``,
``Bundle.unbundle``).

A typed dynamic namespace on a task INPUT (``datasets: Annotated[dict,
dynamic(SnapshotDataset)]``) killed a live workflow on that path with
``ValueError: Namespace structures do not match for linking: ... Missing in
source: []. Missing in target: []`` -- both lists empty, because the check that
failed was namespace-vs-leaf on a child the message cannot name -- while
``from_dict(to_dict())`` on that exact graph succeeded. That failure does NOT
reproduce on this version: the same shape round-trips, runs, and survives the
checkpoint bundle. It is pinned below as a guard rather than dropped, since the
shape is the one that broke. See
``proposed-issues/14-aiida-workgraph-two-serialization-paths.md`` for the
grading.

Two wishes: that the round-trip every graph shape gets were the engine's
serialization (today ``to_engine_inputs()`` is, and nothing points a test author
at it), and an error message that names the child that mismatched.

Each ``# mwe:`` region below is one example in ``docs/index.rst`` and must
read on its own, so a definition two regions share is repeated in each,
identically; the tests bind the last copy.
"""

import json
from enum import Enum
from typing import Annotated, TypedDict

import pytest
from aiida_workgraph import WorkGraph, dynamic, namespace, task


# mwe: to-dict-live
class SpinType(Enum):
    COLLINEAR = "collinear"


def test_to_dict_returns_live_objects(aiida_profile):
    @task
    def leaf(spin):
        return str(spin)

    @task.graph
    def top(spin: SpinType):
        leaf(spin=spin)

    data = top.build(spin=SpinType.COLLINEAR).to_dict()
    assert data["tasks"]["graph_inputs"]["inputs"]["spin"] is SpinType.COLLINEAR
    with pytest.raises(TypeError):
        json.dumps(data)


# end mwe: to-dict-live


# mwe: round-trip-runs
class SpinType(Enum):
    COLLINEAR = "collinear"


def test_engine_inputs_catch_what_the_round_trip_misses(aiida_profile):
    @task
    def leaf(spin):
        return str(spin)

    @task.graph
    def top(spin: SpinType):
        leaf(spin=spin)

    graph = top.build(spin=SpinType.COLLINEAR)
    WorkGraph.from_dict(graph.to_dict())  # the guard every graph shape gets: passes
    with pytest.raises(ValueError, match="Cannot serialize the provided object"):
        graph.to_engine_inputs()  # what run() serializes through, without a run


# end mwe: round-trip-runs


# mwe: checkpoint-path
class Dataset(TypedDict):
    x: int
    y: int


@task
def extract(seed: int) -> Annotated[dict, namespace(x=int, y=int)]:
    return {"x": seed, "y": seed * 2}


@task
def train(datasets: Annotated[dict, dynamic(Dataset)]) -> int:
    return len(dict(datasets))


@task.graph
def fan_into_dynamic_namespace(seed: int):
    """The shape that died on the daemon: a fan-out into a typed dynamic input."""
    datasets = {f"snap_{i}": extract(seed=seed + i) for i in range(2)}
    return train(datasets=datasets).result


def test_the_checkpoint_path_can_be_driven_without_a_daemon(aiida_profile):
    import plumpy.persistence
    from aiida.engine.persistence import AiiDAPersister, get_object_loader
    from aiida.engine.utils import instantiate_process
    from aiida.manage import get_manager
    from aiida_workgraph.engine.workgraph import WorkGraphEngine
    from aiida_workgraph.utils import restore_workgraph_data_from_raw_inputs

    graph = fan_into_dynamic_namespace.build(seed=1)
    graph.check_before_run()

    runner = get_manager().get_runner()
    process = instantiate_process(runner, WorkGraphEngine, **graph.to_engine_inputs())

    persister = AiiDAPersister()
    persister.save_checkpoint(process)
    process.close()

    context = plumpy.persistence.LoadSaveContext(loader=get_object_loader(), runner=runner)
    restored = persister.load_checkpoint(process.pid).unbundle(context)

    WorkGraph.from_dict(restore_workgraph_data_from_raw_inputs(dict(restored.inputs)))
    restored.setup()


# end mwe: checkpoint-path


def test_typed_dynamic_namespace_round_trips_and_runs(aiida_profile):
    """GUARD: the shape that died on the daemon passes both in-process checks.

    On this version the fan-out into a TypedDict-typed dynamic input namespace
    both round-trips and runs, so the failure it once caused is not visible
    here. Pinned rather than dropped, because the shape is the one that broke.
    """
    graph = fan_into_dynamic_namespace.build(seed=1)
    WorkGraph.from_dict(graph.to_dict())
    graph.run()
    assert graph.outputs.result.value == 2
