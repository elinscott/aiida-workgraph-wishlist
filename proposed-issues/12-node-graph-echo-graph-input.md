REPO: scinode/node-graph

TITLE: Returning a graph input as a graph output is rejected eagerly and accepted deferred

BODY:
## Description

A `@task.graph` often wants to surface a value it was handed, and the natural spelling is `return {"payload": payload}`. Whether that is legal depends on where the caller put the graph.

Built at the top level, the body runs eagerly, its `dict` input is a proxy over a plain `dict`, and the return-payload check walks into it until it finds a raw leaf: `TypeError: Invalid graph return payload. - Location: outputs.payload.a - Got: int - Expected: BaseSocket (a task's socket) or TaggedValue`. Called as a node inside another graph, the body runs deferred, the same input is a proxy over `orm.Dict`, the check treats it as one leaf, and the identical line is accepted. A scalar input echoes fine on both paths.

So the discriminator is the incidental wrapper, not the value, and the body's author does not choose it. The message's advice — wrap the computation in a task and return its output socket — does not fit a value that was never computed in this graph.

The cost, in one workflow package: four tasks exist only to launder a value through a function that returns it unchanged, and one output namespace is shaped around the rule rather than around the data, because the step that consumed a value cannot re-emit it.

## MWE

```python
from typing import Annotated

from aiida_workgraph import namespace, task


@task
def make_payload() -> dict:
    return {"a": 1}


@task.graph
def echo_dict(payload: dict) -> Annotated[dict, namespace(payload=dict)]:
    return {"payload": payload}


# Eager: refused.
echo_dict.build(payload={"a": 1})
# TypeError: Invalid graph return payload.
#   - Location: outputs.payload.a
#   - Got: int

# Deferred: the same graph, the same body, accepted.
@task
def sink(payload) -> dict:
    return {"a": dict(payload)["a"]}


@task.graph
def top():
    sink(payload=echo_dict(payload=make_payload().result).payload)


top.build().run()        # fine
```

## Wish

Echoing an input should behave the same way wherever the graph is called: either it works as a passthrough link, or it is refused identically on both paths with a message that says what to do with a value the graph did not compute.

Both halves were reproduced against node-graph 0.6.5 with aiida-workgraph 0.9.0 (main @ 502c1b5b).
