"""Node-vs-value surprises at task boundaries.

These are the "had to do something odd" cases from aiida-koopmans2 that are
*surprising defaults* rather than outright bugs -- documented here as passing
guards so the behaviour is pinned and discoverable (with the workaround in the
assertion / comment). The genuine wish among them is the inconsistency in #3.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from aiida.orm import Int
from aiida_workgraph import namespace, task


class PlainEnum(Enum):
    """Module-level (importable) so EnumData can record its identifier."""

    A = "a"


def test_str_of_node_is_repr_not_value():
    """``str(node)`` returns a ``uuid: ... value: ...`` repr, NOT the value.

    Bit us via a QueryBuilder filter (`aiida-koopmans2/utils.py`): use ``.value``.
    """
    from aiida.orm import Str

    s = Str("hello")
    assert str(s).startswith("uuid:")  # the footgun
    assert s.value == "hello"  # the fix


def test_enum_coerces_to_enumdata_not_str():
    """A plain Enum becomes ``EnumData``, not ``orm.Str``.

    A builder port that wants ``orm.Str`` must pass ``member.value``
    (`aiida-koopmans2/workgraphs/wannier90.py`).
    """
    from aiida.orm.nodes.data.base import to_aiida_type
    from aiida.orm.nodes.data.enum import EnumData

    # A plain Enum (like aiida-wannier90's WannierProjectionType) -> EnumData.
    assert isinstance(to_aiida_type(PlainEnum.A), EnumData)


def test_task_body_receives_deserialized_payload(aiida_profile):
    """A ``@task`` body gets the DESERIALIZED payload (ase.Atoms), not the node.

    To keep the node (e.g. to call ``family.get_pseudos(structure=...)``) you must
    register a passthrough deserializer (`aiida-koopmans2/utils.py`
    ``KOOPMANS_NODE_DESERIALIZERS``). For unknown Data types the default
    deserializer raises instead.
    """
    from aiida.orm import StructureData
    from ase.build import bulk

    @task
    def what_type(s):
        return type(s).__name__

    @task.graph
    def top():
        return what_type(s=StructureData(ase=bulk("Si", "diamond", 5.43))).result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == "Atoms"


def test_workfunction_needed_to_emit_an_existing_node(aiida_profile):
    """To emit an already-stored node you must use ``@task.workfunction``.

    A plain ``@task`` (calcfunction-style) raises "cannot return data ... use a
    @workfunction instead". This is why aiida-koopmans2 resolves pseudos
    (existing ``UpfData`` from a family group) via a ``@task.workfunction``.
    """
    pk = Int(909).store().pk

    @task.workfunction()
    def pick() -> Int:
        from aiida.orm import load_node

        return load_node(pk)

    @task.graph
    def top():
        return pick().result

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == 909


# mwe: scalar-dot-value
def test_scalar_input_in_graph_body_needs_dot_value(aiida_profile):
    @task
    def make() -> str:
        return "777"

    @task
    def seen(x):
        return x

    @task.graph
    def inner(label) -> Annotated[dict, namespace(naive_ok=bool, via_value=int)]:
        try:
            int(label)  # naive conversion of the scalar input
            naive_ok = True
        except TypeError:
            naive_ok = False
        return {"naive_ok": seen(x=naive_ok).result, "via_value": seen(x=int(label.value)).result}

    @task.graph
    def top() -> Annotated[dict, namespace(naive_ok=bool, via_value=int)]:
        return inner(label=make().result)

    graph = top.build()
    graph.run()
    assert not graph.outputs.naive_ok.value  # the footgun: cannot use the scalar directly
    assert graph.outputs.via_value.value == 777  # .value is the way through


# end mwe: scalar-dot-value
