REPO: aiidateam/aiida-workgraph

TITLE: A body does not receive the Python types its signature declares, and which types it receives depends on the call site

BODY:
## Description

A `@task` or `@task.graph` body is ordinary Python written against the types in its own signature. On aiida-workgraph 0.9.0 (main @ 502c1b5b) with node-graph 0.6.5, what arrives depends both on which kind of body it is and on where the caller put the graph:

- A dataclass socket is rebuilt faithfully in a `@task` body — `type(cfg.nspin)` is `int`. In a `@task.graph` body the same field is a proxy over `orm.Int`, so `range(cfg.nspin)` raises `TypeError: 'Int' object cannot be interpreted as an integer` (#780).
- A `dict` input is a proxy over a plain `dict` when the body runs eagerly and over `orm.Dict` when it runs deferred, so `isinstance(d, dict)` answers differently for the identical line. Which one a body gets is the caller's choice, not the author's.
- A `None`-valued field of a `TypedDict` socket is dropped in transit: the far side sees the key absent, with no error, so a value that is legitimately `None` is indistinguishable from one never set (#779). Modelling the same shape as a dataclass was our documented way around this — and it no longer builds: an `Optional` field left at its default, or passed explicitly as `None`, is reported as `ValueError: Missing required inputs: graph_inputs.cfg.tot_magnetization`.
- An `orm` node a body needs whole cannot reach a plain `@task` at all: `ValueError: Cannot deserialize AiiDA data of type ...SinglefileData. This type does not define a '.value' attribute`. Only a `@task.calcfunction` receives it, which costs a process node and provenance for work that is not a calculation (aiidateam/aiida-pythonjob#78, #83).

Each of these is individually small; together they mean a body's signature is not a contract, and the workarounds — `int(x)`, `dict((x or {}).items())`, non-`None` sentinels, a calcfunction where a function was wanted — are written at call sites rather than declared once.

## MWE

```python
from dataclasses import dataclass
from typing import Optional

from aiida_workgraph import task


@dataclass
class Settings:
    nspin: int = 1
    tot_magnetization: Optional[float] = None


@task
def leaf(cfg: Settings) -> dict:
    return {"nspin_type": type(cfg.nspin).__name__}      # 'int' — correct


@task.graph
def inner(cfg: Settings):
    list(range(cfg.nspin))     # TypeError: 'Int' object cannot be interpreted as an integer


@task.graph
def top(cfg: Settings):
    leaf(cfg=cfg)
    inner(cfg=cfg)


top.build(cfg=Settings(nspin=2, tot_magnetization=1.5)).run()

top.build(cfg=Settings())
# ValueError: Missing required inputs:
#   • graph_inputs.cfg.tot_magnetization
```

```python
def looks_like_a_dict(d):
    return isinstance(d, dict)


@task.graph
def deferred(d: dict):
    record(verdict=looks_like_a_dict(d))       # False  (proxy over orm.Dict)


@task.graph
def eager(d: dict):
    record(verdict=looks_like_a_dict(d))       # True   (proxy over dict)
    deferred(d=d)


eager.build(d={"a": 1}).run()
```

## Wish

One delivery contract: a body sees the Python types its signature declares, the same types on every path, with serialization the framework's concern. A `None` field is a field; an `int` field is an `int`; a field with a default is optional; and a body can declare that it wants the node rather than the node's value.

Every observation above was reproduced against aiida-workgraph 0.9.0 (main @ 502c1b5b), node-graph 0.6.5, aiida-pythonjob 0.5.2, aiida-core 2.7.3.

Related: #779, #780, aiidateam/aiida-pythonjob#78, aiidateam/aiida-pythonjob#83.
