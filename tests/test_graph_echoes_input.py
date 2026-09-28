"""Whether a graph may echo its own input back out depends on the wrapper.

A ``@task.graph`` often wants to surface a value it was handed: the alphas a
screening step was run at, the model a prediction used, a folder the caller
supplied. The natural spelling is ``return {"payload": payload}``.

Empirically (aiida-workgraph 0.9.0, upstream main @ 502c1b5b; node-graph 0.6.5)
it works or raises depending on things the body's author did not choose:

* a scalar input echoes fine -> PASS;
* a ``dict`` input echoed from a body that ran EAGERLY raises ``TypeError:
  Invalid graph return payload. - Location: outputs.payload.a - Got: int``
  -> WISH;
* the same graph invoked as a node, so its body runs DEFERRED, echoes the same
  ``dict`` without complaint -> PASS.

The discriminator is what the value is wrapped in, not what it is. A deferred
body's ``dict`` input is a proxy over ``orm.Dict``, which the return-payload
check treats as one leaf; an eager body's is a proxy over a plain ``dict``,
which it walks into until it finds a raw ``int`` and refuses. So the same line
of code is legal or illegal according to where the caller put the graph.

What it costs: four tasks in aiida-koopmans2 exist only to launder a value
through a task that returns it unchanged (``echo_alpha_screening``,
``echo_trial_output_parameters``, ``emit_namespace_dict_field``,
``EvaluateOutputs.model``), and one output namespace is shaped around the rule
rather than around the data (``KoopmansDSCFOutputs.alphas`` is wired at the
outer workflow level because the step that used it cannot re-emit it).

Wish: echoing an input should either work as a passthrough link, or fail the
same way wherever the graph is called.

NOTE: deliberately no ``from __future__ import annotations`` -- the namespace
return annotations below are read at runtime.
"""

from typing import Annotated

import pytest
from aiida import orm
from aiida_workgraph import namespace, task


@task
def make_payload() -> dict:
    return {"a": 1}


def _tagged(tag):
    return [
        node.get_dict()
        for (node,) in orm.QueryBuilder().append(orm.Dict).all()
        if node.get_dict().get("_tag") == tag
    ]


def test_scalar_input_echoes(aiida_profile):
    """GUARD: returning a scalar graph input as an output works."""

    @task.graph
    def echo_scalar(label: str) -> Annotated[dict, namespace(label=str)]:
        return {"label": label}

    graph = echo_scalar.build(label="x")
    graph.run()
    # The output is the orm node, not the str -- see test_node_and_serialization.
    assert graph.outputs.label.value.value == "x"


# mwe: echo-dict-eager
@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: returning a "
    "`dict` graph input from an eagerly-run body raises `TypeError: Invalid graph "
    "return payload. - Location: outputs.payload.a - Got: int - Expected: BaseSocket "
    "(a task's socket) or TaggedValue`. The check walks into the plain dict and "
    "judges its leaves, although the dict as a whole is a legitimate tagged input. "
    "The identical graph called as a node succeeds (see the guard below), so the "
    "error is about the wrapper, not the value, and the message's advice -- wrap the "
    "computation in a task -- does not fit a value that was never computed here. We "
    "wish echoing an input worked, or failed the same way on both paths. "
    "(Documented escape hatch: a passthrough @task that returns its argument.)"
)
def test_dict_input_echoes_from_an_eager_body(aiida_profile):
    """WISH: ``return {"payload": payload}`` works at the top level too."""

    @task.graph
    def echo_dict(payload: dict) -> Annotated[dict, namespace(payload=dict)]:
        return {"payload": payload}

    graph = echo_dict.build(payload={"a": 1})
    graph.run()
    assert dict(graph.outputs.payload.value) == {"a": 1}


# end mwe: echo-dict-eager


def test_dict_input_echoes_from_a_deferred_body(aiida_profile):
    """GUARD: the same echo, one level down, is accepted.

    Pinned because it is the negative control for the wish above: the value and
    the code are identical, only the call site moved.
    """

    @task.graph
    def echo_dict(payload: dict) -> Annotated[dict, namespace(payload=dict)]:
        return {"payload": payload}

    @task
    def sink(payload) -> dict:
        return {"_tag": "deferred_echo", "a": dict(payload)["a"]}

    @task.graph
    def top():
        sink(payload=echo_dict(payload=make_payload().result).payload)

    top.build().run()
    assert _tagged("deferred_echo")[0]["a"] == 1


# mwe: echo-passthrough
def test_the_passthrough_task_we_ship(aiida_profile):
    """GUARD: laundering the value through a task that returns it unchanged.

    The workaround aiida-koopmans2 writes four times. It costs a process node
    per echo and puts a task in the provenance graph that did no work.
    """

    @task
    def echo(payload: dict) -> dict:
        return payload

    @task.graph
    def workaround(payload: dict) -> Annotated[dict, namespace(payload=dict)]:
        return {"payload": echo(payload=payload).result}

    graph = workaround.build(payload={"a": 1})
    graph.run()
    assert dict(graph.outputs.payload.value) == {"a": 1}


# end mwe: echo-passthrough
