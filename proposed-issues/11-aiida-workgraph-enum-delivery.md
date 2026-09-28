REPO: aiidateam/aiida-workgraph

TITLE: An Enum member cannot be delivered to a task body as itself

BODY:
## Description

Enums are how the AiiDA plugin ecosystem spells a mode — `SpinType.COLLINEAR`, `ElectronicType.INSULATOR`, `WannierProjectionType.ATOMIC_PROJECTORS_QE` — and a workflow that wraps those plugins has to carry members from its own inputs down to their builders. On aiida-workgraph 0.9.0 (main @ 502c1b5b) with node-graph 0.6.5 there is no path on which you write the member and read the member back:

1. A bare member as a socket value builds fine and dies at run: `Cannot serialize the provided object. Type: <module>.SpinType — not found in provided serializers`. `aiida_pythonjob.data.serializer.general_serializer` keys its registry on the exact `module.ClassName` and never walks the MRO, so no entry covers `enum.Enum`, although `aiida.orm.to_aiida_type` already maps any member to `EnumData`.
2. Nested inside a `dict` input it is refused with `type <enum 'SpinType'> is not supported as it is not json-serializable` — loud, and the right answer.
3. Wrapped by hand as `orm.EnumData(member)` it crosses, and then delivers two different things: a `@task.graph` body gets a `TaggedValue` proxy over the node, where `spin == SpinType.COLLINEAR` is True but `spin is SpinType.COLLINEAR` is False; a plain `@task` body gets the bare `str` `'collinear'`, where even `==` is False.

Case 3 is the expensive one because it is silent. `aiida-quantumespresso`'s `PwBaseWorkChain.get_builder_from_protocol` branches on `electronic_type is ElectronicType.INSULATOR`; forwarded from a graph body that test is False, the builder takes its metal branch, and every scf and nscf runs `occupations='smearing', smearing='cold', degauss=0.02`. No error, no warning, wrong physics — we found it after six months of stored calculations.

The workaround we now apply at every body that forwards an Enum is `enum_cls(getattr(value, "value", value))`. It works on both shapes, which is exactly why it gets applied blindly, and it silently accepts a member of a *different* Enum whose value happens to match.

## MWE

```python
from enum import Enum

from aiida import orm
from aiida_workgraph import task


class SpinType(Enum):
    NONE = "none"
    COLLINEAR = "collinear"


def third_party(spin):                       # stands in for a plugin's builder
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"


@task
def leaf(spin) -> dict:
    return {"type": type(spin).__name__, "eq": spin == SpinType.COLLINEAR}


@task.graph
def top(spin: SpinType):
    print("in the graph body:", third_party(spin))   # -> 'unpolarized'
    leaf(spin=spin)


top.build(spin=SpinType.COLLINEAR).run()
# ValueError: Cannot serialize the provided object. Type: __main__.SpinType

top.build(spin=orm.EnumData(SpinType.COLLINEAR)).run()
# in the graph body: unpolarized      <- silently the wrong branch
# leaf saw: {'type': 'str', 'eq': False}
```

## Wish

Identity is decided by the interpreter, so no proxy can ever make `spin is SpinType.COLLINEAR` true; the fix is not on the proxy but at the boundary: resolve it before the body, or anything the body calls, sees the value. An `Enum` member passed to a socket should arrive at every body as that member: registered in the serializer registry by base class (aiida-core already has `EnumData`), and deserialized back to the member rather than to a node proxy in a graph body or to its `.value` in a task body.

Every observation above was reproduced against aiida-workgraph 0.9.0 (main @ 502c1b5b), node-graph 0.6.5, aiida-pythonjob 0.5.2, aiida-core 2.7.3.

Related: scinode/node-graph#152 (`is` semantics on the proxy), scinode/node-graph#176 (what an Enum-typed input should receive), scinode/node-graph#178 and #800 (membership decided twice, on two representations), scinode/node-graph#175 (`Literal[...]` narrowing is dropped, so a socket cannot even be restricted to two members).
