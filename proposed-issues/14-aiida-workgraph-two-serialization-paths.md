REPO: aiidateam/aiida-workgraph

TITLE: A graph can round-trip through to_dict/from_dict and still fail the moment it runs

BODY:
## Description

The obvious way to test that a graph will survive being handed to the engine is `WorkGraph.from_dict(wg.to_dict())`, and we run exactly that as a shared fixture over every graph shape in our package. It is weaker than it looks, for a mechanical reason: `to_dict()` returns a dict of live Python objects. A graph input comes back as the identical object (`data[...]["spin"] is SpinType.COLLINEAR`), and the structure as a whole is not JSON-encodable, so the round-trip exercises no encoder the engine will use. A graph can therefore pass the round-trip and then die at run on the very value the round-trip handed back untouched.

There is a third path neither half reaches by default: the one the daemon takes. `submit()` saves a plumpy checkpoint bundle and a worker unbundles it and steps the process, so the inputs reach `WorkGraphEngine.setup` through `aiida.orm.utils.serialize` rather than arriving live. That path *can* be driven without a daemon, but nothing says so and the recipe is four pieces deep:

```python
process = instantiate_process(get_manager().get_runner(), WorkGraphEngine, **wg.to_engine_inputs())
AiiDAPersister().save_checkpoint(process)
process.close()
context = plumpy.persistence.LoadSaveContext(loader=get_object_loader(), runner=runner)
restored = AiiDAPersister().load_checkpoint(process.pid).unbundle(context)
WorkGraph.from_dict(restore_workgraph_data_from_raw_inputs(dict(restored.inputs)))
restored.setup()
```

That a test author has to assemble this to learn whether their graph will start is the second half of the problem.

Grading, honestly:

- **Reproduced**: `to_dict()` returns live objects, is not JSON-encodable, and a graph passes `from_dict(to_dict())` and then dies at run (the MWE below).
- **Reproduced**: the checkpoint path can be driven in-process with the calls above.
- **Not reproduced on this version**: a typed dynamic namespace on a task input — `datasets: Annotated[dict, dynamic(SnapshotDataset)]`, fanned into from a `@task.graph` loop — killed a live workflow at run start on aiida-workgraph 0.8.1 with `ValueError: Namespace structures do not match for linking: extract_snapshot_dataset.outputs vs train_screening_model.inputs.datasets.snapshot_1. Missing in source: []. Missing in target: []` while `from_dict(to_dict())` on that same graph succeeded. Rebuilt minimally against 0.9.0 the shape round-trips, runs, and survives the checkpoint bundle, so either it was fixed between the two or the minimization misses the trigger. The message itself remains worth fixing whatever the cause: both lists are empty because `node_graph/graph.py:_namespace_structures_match` failed a namespace-vs-leaf comparison on a child it cannot name.

## MWE

```python
import json
from enum import Enum

from aiida_workgraph import WorkGraph, task


class SpinType(Enum):
    COLLINEAR = "collinear"


@task
def leaf(spin) -> dict:
    return {"seen": str(spin)}


@task.graph
def top(spin: SpinType):
    leaf(spin=spin)


graph = top.build(spin=SpinType.COLLINEAR)

data = graph.to_dict()
assert data["tasks"]["graph_inputs"]["inputs"]["spin"] is SpinType.COLLINEAR  # the same object
json.dumps(data)                 # TypeError -- to_dict() is not a serialized form

WorkGraph.from_dict(data)        # passes: the round-trip guard is green
graph.run()                      # ValueError: Cannot serialize the provided object
```

## Wish

Two things, either of which would help:

1. One serialization path a test can exercise — or a supported "encode this graph the way the engine will" check, so a green test means the graph starts.
2. When the namespace comparison fails, name the child that mismatched. `Missing in source: []. Missing in target: []` tells the reader only that the two sides differ in a way the message cannot express.

Reproduced against aiida-workgraph 0.9.0 (main @ 502c1b5b), node-graph 0.6.5, aiida-pythonjob 0.5.2, aiida-core 2.7.3.
