"""The meeting notes page's worked examples: want / today / should-fail, per topic.

``docs/index.rst`` walks three topics (Enums, plain Python in bodies, eager vs
deferred bodies) and for each shows the code we would like to write, the code
we actually write today, and one example that passes today but, once the
underlying wish is granted, ought to start failing. This module backs those
nine snippets.

Each ``# mwe:`` region is one example in ``docs/index.rst`` and must read on
its own, so a definition shared by two regions is repeated in each,
identically; the tests bind the last copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pytest
from aiida import orm
from aiida_workgraph import task


@task
def seen(x):
    return x


# ----------------------------------------------------------------------
# 1. Enums
# ----------------------------------------------------------------------


# mwe: enum-want
class SpinType(Enum):
    NONE = "none"
    COLLINEAR = "collinear"


@task
def classify(spin) -> str:
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a bare Enum member cannot cross "
    "a socket at all -- `graph.run()` raises `ValueError: Cannot serialize the "
    "provided object. Type: ...SpinType ... not found in provided serializers`. "
    "This is the code we want: a member in, a member out, with `is` doing the "
    "right thing inside `classify`."
)
def test_enum_want(aiida_profile):
    @task.graph
    def top(spin: SpinType):
        return classify(spin=spin).result

    graph = top.build(spin=SpinType.COLLINEAR)
    graph.run()  # today: ValueError: Cannot serialize the provided object. Type: ...SpinType
    assert graph.outputs.result.value == "polarized"


# end mwe: enum-want


# mwe: enum-today
class SpinType(Enum):
    NONE = "none"
    COLLINEAR = "collinear"


@task
def classify(spin) -> str:
    return "polarized" if spin == "collinear" else "unpolarized"


def test_enum_today(aiida_profile):
    @task.graph
    def top(spin: SpinType):
        spin = SpinType(getattr(spin, "value", spin))  # proxy over EnumData -> member
        return classify(spin=spin.value).result  # member -> str: a member cannot cross a socket

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))
    graph.run()
    assert graph.outputs.result.value == "polarized"


# end mwe: enum-today


# mwe: enum-should-fail
class SpinType(Enum):
    NONE = "none"
    COLLINEAR = "collinear"


def test_enum_should_fail(aiida_profile):
    @task.graph
    def inner(spin: SpinType):
        return seen(x=spin.get_member() is SpinType.COLLINEAR).result

    @task.graph
    def top(spin: SpinType):
        return inner(spin=spin).result

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because spin is a proxy over orm.EnumData, which forwards .get_member()
    # wanted: AttributeError: 'SpinType' object has no attribute 'get_member'


# end mwe: enum-should-fail


# ----------------------------------------------------------------------
# 2. Plain Python in bodies
# ----------------------------------------------------------------------


# mwe: int-want
@dataclass
class Settings:
    nspin: int = 1


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): inside a @task.graph body that "
    "runs deferred, a dataclass `int` field is a TaggedValue over `orm.Int`, so "
    "`range(cfg.nspin)` raises `TypeError: 'Int' object cannot be interpreted as an "
    "integer`; the inner task fails and `result` is never set. This is the code we "
    "want: an `int` field is an `int`."
)
def test_int_want(aiida_profile):
    @task.graph
    def inner(cfg: Settings):
        return seen(x=len(range(cfg.nspin))).result

    @task.graph
    def top(cfg: Settings):
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()
    assert graph.outputs.result.value == 2


# end mwe: int-want


# mwe: int-today
@dataclass
class Settings:
    nspin: int = 1


def test_int_today(aiida_profile):
    @task.graph
    def inner(cfg: Settings):
        nspin = int(cfg.nspin)  # orm.Int -> int, or range() fails
        return seen(x=len(range(nspin))).result

    @task.graph
    def top(cfg: Settings):
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()
    assert graph.outputs.result.value == 2


# end mwe: int-today


# mwe: int-should-fail
@dataclass
class Settings:
    nspin: int = 1


def test_int_should_fail(aiida_profile):
    @task.graph
    def inner(cfg: Settings):
        return seen(x=cfg.nspin.value).result

    @task.graph
    def top(cfg: Settings):
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()
    assert graph.outputs.result.value == 2
    # today: passes, because cfg.nspin is a proxy over orm.Int, which has .value
    # wanted: AttributeError: 'int' object has no attribute 'value'


# end mwe: int-should-fail


# ----------------------------------------------------------------------
# 3. Eager and deferred bodies
# ----------------------------------------------------------------------


# mwe: dict-want
@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a `dict` input reaching a "
    "deferred body is a TaggedValue over `orm.Dict`, so `isinstance(overrides, "
    "dict)` is False. The identical code at the top level, where the body runs "
    "eagerly, would see a plain `dict`. This is the code we want: one delivery "
    "contract regardless of where the graph sits in the call tree."
)
def test_dict_want(aiida_profile):
    @task.graph
    def inner(overrides: dict):
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict):
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value


# end mwe: dict-want


# mwe: dict-today
def test_dict_today(aiida_profile):
    @task.graph
    def inner(overrides: dict):
        overrides = dict(overrides.items())  # proxy over orm.Dict -> dict
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict):
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value


# end mwe: dict-today


# mwe: dict-should-fail
def test_dict_should_fail(aiida_profile):
    @task.graph
    def inner(overrides: dict):
        return seen(x=overrides.get_dict() == {"ecutwfc": 40}).result

    @task.graph
    def top(overrides: dict):
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value
    # today: passes, because overrides is a proxy over orm.Dict, which has .get_dict()
    # wanted: AttributeError: 'dict' object has no attribute 'get_dict'


# end mwe: dict-should-fail
