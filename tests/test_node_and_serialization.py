"""Node-vs-value surprises at task boundaries.

These are the "had to do something odd" cases from aiida-koopmans2 that are
*surprising defaults* rather than outright bugs -- documented here as passing
guards so the behaviour is pinned and discoverable (with the workaround in the
assertion / comment). The genuine wish among them is the inconsistency in #3.
"""

from __future__ import annotations

from enum import Enum

from aiida.orm import Int
from aiida_workgraph import task


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


def test_task_body_receives_deserialized_payload(collect):
    """A ``@task`` body gets the DESERIALIZED payload (ase.Atoms), not the node.

    To keep the node (e.g. to call ``family.get_pseudos(structure=...)``) you must
    register a passthrough deserializer (`aiida-koopmans2/utils.py`
    ``KOOPMANS_NODE_DESERIALIZERS``). For unknown Data types the default
    deserializer raises instead.
    """
    from aiida.orm import StructureData
    from ase.build import bulk

    @task
    def what_type(s) -> dict:
        return {"_tag": "deser", "got": type(s).__name__}

    @task.graph
    def top():
        what_type(s=StructureData(ase=bulk("Si", "diamond", 5.43)))

    [r] = collect(top, "deser")
    assert r["got"] == "Atoms"


def test_workfunction_needed_to_emit_an_existing_node(collect):
    """To emit an already-stored node you must use ``@task.workfunction``.

    A plain ``@task`` (calcfunction-style) raises "cannot return data ... use a
    @workfunction instead". This is why aiida-koopmans2 resolves pseudos
    (existing ``UpfData`` from a family group) via a ``@task.workfunction``.
    """
    pre = Int(909)
    pre.store()
    pk = pre.pk

    @task.workfunction()
    def pick() -> Int:
        from aiida.orm import load_node

        return load_node(pk)

    @task
    def sink(v) -> dict:
        return {"_tag": "wf", "v": int(v)}

    @task.graph
    def top():
        sink(v=pick().result)

    [r] = collect(top, "wf")
    assert r["v"] == 909


# mwe: scalar-dot-value
def test_scalar_input_in_graph_body_needs_dot_value(collect):
    """A scalar input inside a ``@task.graph`` body is a proxy over an ``orm`` node.

    Inconsistency worth raising: a *dict* input arrives as a plain dict you can
    subscript (see ``test_graph_body_values``), but a *str* input is a tagged
    proxy over ``orm.Str`` -- so naive ``int(label)`` raises and you must reach
    through ``.value``.
    """

    @task
    def make() -> str:
        return "777"

    @task
    def sink(naive_ok, via_value) -> dict:
        return {"_tag": "scalar", "naive_ok": naive_ok, "via_value": via_value}

    @task.graph
    def inner(label):
        try:
            int(label)  # naive conversion of the scalar input
            naive_ok = True
        except Exception:
            naive_ok = False
        sink(naive_ok=naive_ok, via_value=int(label.value))

    @task.graph
    def top():
        inner(label=make().result)

    [r] = collect(top, "scalar")
    assert r["naive_ok"] is False  # the footgun: cannot use the scalar directly
    assert r["via_value"] == 777  # .value is the way through


# end mwe: scalar-dot-value
