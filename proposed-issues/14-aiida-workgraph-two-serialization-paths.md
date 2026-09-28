REPO: aiidateam/aiida-workgraph

TITLE: A graph can round-trip through to_dict/from_dict and still fail the moment it runs

BODY:
## Description

The obvious way to test that a graph will survive being handed to the engine is `WorkGraph.from_dict(wg.to_dict())`, and we run exactly that as a shared fixture over every graph shape in our package. It is weaker than it looks, for a mechanical reason: `to_dict()` returns a dict of live Python objects. A graph input comes back as the identical object (`data[...]["spin"] is SpinType.COLLINEAR`), and the structure as a whole is not JSON-encodable, so the round-trip exercises no encoder the engine will use. A graph can therefore pass the round-trip and then die at run on the very value the round-trip handed back untouched.

There is a third path neither half reaches. On launch the daemon persists `task_inputs` to the database and rebuilds them in `WorkGraphEngine.setup` via `restore_workgraph_data_from_raw_inputs` (`aiida_workgraph/utils/__init__.py:351`); an in-process `run()` reaches that same function with the live inputs, so the database encode/decode never happens. A typed dynamic namespace on a task *input* — `datasets: Annotated[dict, dynamic(SnapshotDataset)]` — killed a live workflow there with

```
ValueError: Namespace structures do not match for linking:
  extract_snapshot_dataset.outputs vs train_screening_model.inputs.datasets.snapshot_1.
  Missing in source: []. Missing in target: [].
```

Both lists are empty because `node_graph/graph.py:_namespace_structures_match` failed a namespace-vs-leaf comparison on a child, and the message has no way to name which one. `from_dict(to_dict())` on that exact graph succeeded in-process.

Grading, honestly: the round-trip weakness and the run-time failure that follows it are **reproduced** (see the MWE). The daemon-only failure above is **observed in production but not reduced to a minimal example** — we could not drive the database round-trip of `task_inputs` without a daemon. Reproduction recipe, for anyone with a daemon to hand: build a fan-out whose per-entry producer is a namespace-valued task and whose consumer declares `Annotated[dict, dynamic(SomeTypedDict)]`, assert `WorkGraph.from_dict(wg.to_dict())` succeeds, then `wg.submit()` it and read the engine's exception from the process report. The empty `Missing in source` / `Missing in target` lists are the signature.

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
