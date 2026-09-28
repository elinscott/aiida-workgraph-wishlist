"""A body should see the Python types its signature declares.

A ``@task`` or ``@task.graph`` body is ordinary Python: it declares ``cfg:
Settings``, ``d: dict``, ``f: SinglefileData``, and the code inside is written
against those types. Empirically (aiida-workgraph 0.9.0, upstream main @
502c1b5b; node-graph 0.6.5) what actually arrives depends on which kind of body
you are in and on which path the graph was invoked:

* in a ``@task`` body a dataclass socket is rebuilt faithfully, ``int`` fields
  and all -> PASS (the guard that makes the next case a defect, not a policy);
* in a ``@task.graph`` body the same field is a proxy over ``orm.Int``, so
  ``range(cfg.nspin)`` raises -> WISH;
* a ``dict`` input is a proxy over a plain ``dict`` when the body runs eagerly
  and over ``orm.Dict`` when it runs deferred, so ``isinstance(d, dict)``
  answers differently for the same code -> WISH;
* a ``None``-valued field of a ``TypedDict`` socket is gone on the far side,
  while a dataclass keeps it -> WISH;
* and the dataclass escape hatch is itself broken: an ``Optional`` field left at
  its default, or passed explicitly as ``None``, is reported as a *missing
  required input* -> WISH;
* an ``orm`` node a body needs whole (``SinglefileData``, ``FolderData``) cannot
  reach a plain ``@task`` at all; only a ``@task.calcfunction`` gets it -> WISH
  plus its guard.

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
from typing import Optional, TypedDict

import pytest
from aiida import orm
from aiida_workgraph import task


def _tagged(tag):
    return [
        node.get_dict()
        for (node,) in orm.QueryBuilder().append(orm.Dict).all()
        if node.get_dict().get("_tag") == tag
    ]


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
    """WISH: ``tot_magnetization=None`` is still a key on the far side."""

    @task
    def leaf(cfg: SettingsTypedDict) -> dict:
        return {"_tag": "td_none", "detail": ",".join(sorted(dict(cfg)))}

    @task.graph
    def top(cfg: SettingsTypedDict):
        leaf(cfg=cfg)

    top.build(cfg=SettingsTypedDict(nspin=1, tot_magnetization=None)).run()
    assert _tagged("td_none")[0]["detail"] == "nspin,tot_magnetization"


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
    """WISH: a dataclass at its own defaults builds."""

    @task
    def leaf(cfg: Settings) -> dict:
        return {"_tag": "dc_default", "detail": repr(cfg.tot_magnetization)}

    @task.graph
    def top(cfg: Settings):
        leaf(cfg=cfg)

    top.build(cfg=Settings()).run()
    assert _tagged("dc_default")[0]["detail"] == "None"


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
def record(tag, detail) -> dict:
    return {"_tag": tag, "detail": detail}


def test_task_body_rebuilds_the_dataclass(aiida_profile):
    """GUARD: a ``@task`` body gets a real ``Settings`` with real ``int`` fields.

    This is the behaviour the next test wishes for one level up.
    """

    @task
    def leaf(cfg: Settings) -> dict:
        return {"_tag": "task_dc", "detail": f"{type(cfg).__name__}/{type(cfg.nspin).__name__}"}

    @task.graph
    def top(cfg: Settings):
        leaf(cfg=cfg)

    top.build(cfg=Settings(nspin=2, tot_magnetization=1.5)).run()
    assert _tagged("task_dc")[0]["detail"] == "Settings/int"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): inside a @task.graph body a "
    "dataclass socket's `int` field is a TaggedValue over `orm.Int`, which has no "
    "`__index__`, so `range(cfg.nspin)` raises `TypeError: 'Int' object cannot be "
    "interpreted as an integer`. A plain @task body gets a real `int` from the same "
    "socket (see the guard above). We wish an `int` field were an `int` in both. "
    "(Escape hatch: `int(cfg.nspin)` at every use.) Upstream #780."
)
def test_graph_body_int_field_is_an_int(aiida_profile):
    """WISH: ``range(cfg.nspin)`` works in a graph body."""

    @task.graph
    def inner(cfg: Settings):
        record(tag="graph_dc", detail=str(list(range(cfg.nspin))))

    @task.graph
    def top(cfg: Settings):
        inner(cfg=cfg)

    top.build(cfg=Settings(nspin=2, tot_magnetization=1.5)).run()
    assert _tagged("graph_dc")[0]["detail"] == "[0, 1]"


# end mwe: int-field


# ----------------------------------------------------------------------
# The same body, two languages: eager vs deferred
# ----------------------------------------------------------------------


# mwe: dict-input
@task
def record(tag, detail) -> dict:
    return {"_tag": tag, "detail": detail}


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
    """WISH: a ``dict`` input is a ``dict`` wherever the body runs."""

    def looks_like_a_dict(d):
        return isinstance(d, dict)

    @task.graph
    def inner(d: dict):
        record(tag="deferred_dict", detail=str(looks_like_a_dict(d)))

    @task.graph
    def top(d: dict):
        record(tag="eager_dict", detail=str(looks_like_a_dict(d)))
        inner(d=d)

    top.build(d={"a": 1}).run()
    assert _tagged("eager_dict")[0]["detail"] == "True"
    assert _tagged("deferred_dict")[0]["detail"] == "True"


# end mwe: dict-input


# ----------------------------------------------------------------------
# An orm node a body needs whole
# ----------------------------------------------------------------------


# mwe: file-node
@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / aiida-pythonjob 0.5.2: a "
    "`SinglefileData` input to a plain @task fails at run with `ValueError: Cannot "
    "deserialize AiiDA data of type ...SinglefileData. This type does not define a "
    "`.value` attribute, and no matching deserializer was provided`. Any node whose "
    "content is not a scalar -- SinglefileData, FolderData, RemoteData -- is "
    "therefore unreachable from a plain function task. We wish a body could declare "
    "it wants the node. (Documented escape hatch: make the task a "
    "@task.calcfunction, which costs a process node and provenance you may not want "
    "-- see the guard below.) Upstream aiida-pythonjob #78, #83."
)
def test_plain_task_can_take_a_file_node(aiida_profile, tmp_path):
    """WISH: a plain ``@task`` body can be handed a ``SinglefileData``."""
    path = tmp_path / "input.txt"
    path.write_text("hello")
    node = orm.SinglefileData(file=str(path))
    node.store()

    @task
    def leaf(f) -> dict:
        return {"_tag": "sfd_task", "detail": f.get_content()}

    @task.graph
    def top(f):
        leaf(f=f)

    top.build(f=node).run()
    assert _tagged("sfd_task")[0]["detail"] == "hello"


# end mwe: file-node


def test_calcfunction_is_the_only_way_to_a_file_node(aiida_profile, tmp_path):
    """GUARD: a ``@task.calcfunction`` receives the real node.

    This is why aiida-koopmans2 declares a calcfunction wherever a body needs a
    folder or a file, even when nothing about the work is a calculation.
    """
    path = tmp_path / "input.txt"
    path.write_text("hello")
    node = orm.SinglefileData(file=str(path))
    node.store()

    @task.calcfunction
    def leaf(f) -> orm.Dict:
        return orm.Dict({"_tag": "sfd_calcfunction", "detail": f.get_content()})

    @task.graph
    def top(f):
        leaf(f=f)

    top.build(f=node).run()
    assert _tagged("sfd_calcfunction")[0]["detail"] == "hello"
