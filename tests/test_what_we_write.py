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


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a bare Enum member cannot cross a socket")
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
        return classify(spin=spin.value).result  # member -> str before it crosses a socket

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))  # a bare member cannot cross a socket
    graph.run()
    assert graph.outputs.result.value == "polarized"


# end mwe: enum-today


# mwe: enum-should-fail
@task
def seen(x):
    return x


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
@task
def seen(x):
    return x


@dataclass
class Settings:
    nspin: int = 1


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Int for an int field")
def test_int_want(aiida_profile):
    @task.graph
    def inner(cfg: Settings):
        return seen(x=len(range(cfg.nspin))).result

    @task.graph
    def top(cfg: Settings):
        return inner(cfg=cfg).result

    graph = top.build(cfg=Settings(nspin=2))
    graph.run()  # today: inner fails, TypeError: 'Int' object cannot be interpreted as an integer
    assert graph.outputs.result.value == 2


# end mwe: int-want


# mwe: int-today
@task
def seen(x):
    return x


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
@task
def seen(x):
    return x


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
@task
def seen(x):
    return x


@pytest.mark.xfail(reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): a deferred graph body gets orm.Dict for a dict input")
def test_dict_want(aiida_profile):
    @task.graph
    def inner(overrides: dict):
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict):
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value  # today: False, overrides is an orm.Dict here


# end mwe: dict-want


# mwe: dict-today
@task
def seen(x):
    return x


def test_dict_today(aiida_profile):
    @task.graph
    def inner(overrides: dict):
        overrides = dict(overrides)  # proxy over orm.Dict -> dict
        return seen(x=isinstance(overrides, dict)).result

    @task.graph
    def top(overrides: dict):
        return inner(overrides=overrides).result

    graph = top.build(overrides={"ecutwfc": 40})
    graph.run()
    assert graph.outputs.result.value


# end mwe: dict-today


# mwe: dict-should-fail
@task
def seen(x):
    return x


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
