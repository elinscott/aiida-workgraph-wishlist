"""A body should see the Python types its signature declares.

A ``@task`` or ``@task.graph`` body is ordinary Python: it declares ``cfg:
Settings``, ``d: dict``, ``f: SinglefileData``, and the code inside is written
against those types. Empirically (aiida-workgraph 0.9.0, upstream main @
502c1b5b; node-graph 0.6.5) what actually arrives depends on which kind of body
you are in and on which path the graph was invoked:

* in a ``@task`` body a dataclass socket is rebuilt faithfully, ``int`` fields
  and all -> PASS (the guard that makes the next case a defect, not a policy);
* in a ``@task.graph`` body that runs deferred (called from another graph) the
  same field is a proxy over ``orm.Int``, so ``range(cfg.nspin)`` raises; run
  eagerly, the body gets a proxy over a plain ``int`` and ``range`` works -> WISH;
* a ``dict`` input is a proxy over a plain ``dict`` when the body runs eagerly
  and over ``orm.Dict`` when it runs deferred, so ``isinstance(d, dict)``
  answers differently for the same code -> WISH;
* a ``None``-valued field of a ``TypedDict`` socket is gone on the far side,
  with no error -> WISH;
* and the dataclass escape hatch is itself broken: an ``Optional`` field left at
  its default, or passed explicitly as ``None``, is reported as a *missing
  required input* -> WISH;
* an ``orm`` node a body needs whole (``SinglefileData``, ``FolderData``) cannot
  reach a plain ``@task`` unless a deserializer for its type is registered
  profile-wide in ``pythonjob.json``; per task, only a ``@task.calcfunction``
  gets it -> WISH plus its guard.

The wish, in one sentence: the body sees the Python types its signature
declares, on every path, and serialization is the framework's concern.

Related upstream: aiidateam/aiida-workgraph #779 (``None`` inputs), #780
(boundary promotion of scalars), aiidateam/aiida-pythonjob #78 and #83
(deserializing an ``orm`` node into a body). ``test_none_handling.py`` covers
``None`` as a plain task argument; this module is about structured sockets.

Each ``# mwe:`` region below is one example in ``docs/index.rst`` and must
read on its own, so a definition two regions share is repeated in each,
identically; the tests bind the last copy.

NOTE: deliberately no ``from __future__ import annotations`` -- the dataclass
and TypedDict hints below are read at runtime to build the sockets.
"""

from dataclasses import dataclass
from typing import Annotated, Optional, TypedDict

import pytest
from aiida import orm
from aiida_workgraph import namespace, task


# ----------------------------------------------------------------------
# A None field is a field
# ----------------------------------------------------------------------


# mwe: none-typeddict-field
class SettingsTypedDict(TypedDict, total=False):
    """The settings shape spelled as a TypedDict, the project's standard way."""

    nspin: int
    tot_magnetization: Optional[float]


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a `None`-valued field of a "
    "TypedDict socket is dropped in transit -- the far side sees keys ['nspin'] and "
    "`tot_magnetization` is simply absent, with no error. A closed-shell system "
    "whose `tot_magnetization` is legitimately None is therefore indistinguishable "
    "from one that never set it. We wish a `None` field arrived as a field whose "
    "value is None. (Documented escape hatch: model the shape as a dataclass "
    "instead -- but see the next test for what that costs today.) Upstream #779."
)
def test_none_field_of_a_typeddict_survives(aiida_profile):
    @task
    def leaf(cfg: SettingsTypedDict):
        return "tot_magnetization" in cfg

    @task.graph
    def top(cfg: SettingsTypedDict):
        return leaf(cfg=cfg).result

    graph = top.build(cfg=SettingsTypedDict(nspin=1, tot_magnetization=None))
    graph.run()
    assert graph.outputs.result.value  # today: False -- tot_magnetization is absent from cfg on the far side


# end mwe: none-typeddict-field


# mwe: dataclass-default
@dataclass
class Settings:
    """The shape aiida-koopmans2's ``KcpBaseInputs`` has, minus the physics."""

    nspin: int = 1
    tot_magnetization: Optional[float] = None


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): the dataclass escape hatch no "
    "longer works either. A field with a default -- `tot_magnetization: "
    "Optional[float] = None` -- yields a REQUIRED socket, so building with the "
    "dataclass at its own default raises `ValueError: Missing required inputs: "
    "graph_inputs.cfg.tot_magnetization, leaf.cfg.tot_magnetization`. Passing "
    "`tot_magnetization=None` explicitly raises the same thing, because an explicit "
    "None is dropped first and then reported as absent. We wish a defaulted field "
    "were optional. (Escape hatch: give every Optional field a non-None sentinel, "
    "or carry the shape as one opaque dict value.)"
)
def test_dataclass_default_is_not_a_missing_input(aiida_profile):
    @task
    def leaf(cfg: Settings):
        return cfg.tot_magnetization is None

    @task.graph
    def top(cfg: Settings):
        return leaf(cfg=cfg).result

    graph = top.build(cfg=Settings())
    graph.run()  # today: ValueError: Missing required inputs: graph_inputs.cfg.tot_magnetization, leaf.cfg.tot_magnetization
    assert graph.outputs.result.value


# end mwe: dataclass-default


# ----------------------------------------------------------------------
# A dataclass field: plain in a task body, an orm node in a graph body
# ----------------------------------------------------------------------


# mwe: int-field
@dataclass
class Settings:
    """The shape aiida-koopmans2's ``KcpBaseInputs`` has, minus the physics."""

    nspin: int = 1
    tot_magnetization: Optional[float] = None


@task
def seen(x):
    return x


def test_task_body_rebuilds_the_dataclass(aiida_profile):
    @task
    def leaf(cfg: Settings):
        return type(cfg.nspin).__name__

    @task.graph
    def top(cfg: Settings):
        return leaf(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2, tot_magnetization=1.5))
    graph.run()
    assert graph.outputs.result.value == "int"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): inside a @task.graph body that "
    "runs deferred (called from another graph) a dataclass socket's `int` field is a "
    "TaggedValue over `orm.Int`, so `range(cfg.nspin)` raises `TypeError: 'Int' "
    "object cannot be interpreted as an integer`. The same body run eagerly gets a "
    "TaggedValue over a plain `int`, and a plain @task body gets a real `int` (see "
    "the guard above). We wish an `int` field were an `int` on every path. "
    "(Escape hatch: `int(cfg.nspin)` at every use.) Upstream #780."
)
def test_graph_body_int_field_is_an_int(aiida_profile):
    @task.graph
    def inner(cfg: Settings):
        return seen(x=len(range(cfg.nspin))).result

    @task.graph
    def top(cfg: Settings):
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2, tot_magnetization=1.5))
    graph.run()
    assert graph.outputs.result.value == 2  # today: None -- inner failed with TypeError: 'Int' object cannot be interpreted as an integer


# end mwe: int-field


# ----------------------------------------------------------------------
# The same body, two languages: eager vs deferred
# ----------------------------------------------------------------------


# mwe: dict-input
@task
def seen(x):
    return x


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a `dict` input reaches an "
    "eagerly-run body as a TaggedValue over a plain `dict` and a deferred body as a "
    "TaggedValue over `orm.Dict`, so `isinstance(d, dict)` is True in one and False "
    "in the other for the identical line of code. Which one a body gets is not the "
    "body author's choice -- it depends on whether a caller invoked the graph at top "
    "level or as a node inside another graph. We wish one delivery contract, "
    "independent of where the graph sits in the call tree. (Escape hatch: rebuild "
    "the mapping with `dict((x or {}).items())` before touching it.)"
)
def test_dict_input_is_the_same_on_both_paths(aiida_profile):
    @task.graph
    def inner(d: dict):
        return seen(x=isinstance(d, dict)).result

    @task.graph
    def top(d: dict) -> Annotated[dict, namespace(eager=bool, deferred=bool)]:
        return {"eager": seen(x=isinstance(d, dict)).result, "deferred": inner(d=d).result}

    graph = top.build(d={"a": 1})
    graph.run()
    assert graph.outputs.eager.value
    assert graph.outputs.deferred.value  # today: False -- isinstance(d, dict) is False on the deferred path (d is orm.Dict there)


# end mwe: dict-input


# ----------------------------------------------------------------------
# An orm node a body needs whole
# ----------------------------------------------------------------------


# mwe: file-node
@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / aiida-pythonjob 0.5.2: a "
    "`SinglefileData` input to a plain @task fails at run with `ValueError: Cannot "
    "deserialize AiiDA data of type ...SinglefileData. This type does not define a "
    "`.value` attribute, and no matching deserializer was provided`. `@task` takes "
    "no `deserializers` option and a call-site `deserializers=` is refused as an "
    "undefined input, so the only switch is profile-wide: a pass-through entry for "
    "the type under `deserializers` in `pythonjob.json`, which changes every task in "
    "the profile. We wish a body could declare it wants the node. (Escape hatches: "
    "that profile-wide entry, or make the task a @task.calcfunction, which costs a "
    "process node and provenance you may not want -- see the guard below.) "
    "Upstream aiida-pythonjob #78, #83."
)
def test_plain_task_can_take_a_file_node(aiida_profile):
    @task
    def leaf(f):
        return f.get_content()

    @task.graph
    def top(f):
        return leaf(f=f).result

    graph = top.build(f=orm.SinglefileData.from_string("hello"))
    graph.run()  # today: ValueError: Cannot deserialize AiiDA data of type ...SinglefileData. This type does not define a `.value` attribute
    assert graph.outputs.result.value == "hello"


# end mwe: file-node


def test_calcfunction_receives_a_file_node(aiida_profile):
    """GUARD: a ``@task.calcfunction`` receives the real node.

    This is why aiida-koopmans2 declares a calcfunction wherever a body needs a
    folder or a file, even when nothing about the work is a calculation.
    """

    @task.calcfunction
    def leaf(f):
        return orm.Str(f.get_content())

    @task.graph
    def top(f):
        return leaf(f=f).result

    graph = top.build(f=orm.SinglefileData.from_string("hello"))
    graph.run()
    assert graph.outputs.result.value == "hello"
