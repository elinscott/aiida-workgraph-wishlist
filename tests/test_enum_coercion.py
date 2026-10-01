"""An ``Enum`` member never arrives as itself.

Enums are how upstream AiiDA plugins spell a mode: ``SpinType.COLLINEAR``,
``ElectronicType.INSULATOR``. A workflow that wraps those plugins has to carry
members from its own inputs down to their builders. Empirically (aiida-workgraph
0.9.0, upstream main @ 502c1b5b; node-graph 0.6.5) there is no path on which you
write the member and read the member back:

* a bare member as a socket value cannot be serialized at all -> WISH;
* nested inside a ``dict`` input it is refused at run -> PASS (loud, good);
* wrapped by hand in ``orm.EnumData`` it crosses, and then a ``@task.graph``
  body sees a proxy over the node while a ``@task`` body sees a bare ``str``
  -> two WISHes;
* the socket's declared Enum type is never a membership rule: a member of a
  different Enum, and a member outside a ``Literal[...]`` narrowing, both run
  -> two WISHes.

What the silence costs, reproduced: ``aiida-quantumespresso``'s
``PwBaseWorkChain.get_builder_from_protocol`` branches on ``electronic_type is
ElectronicType.INSULATOR``. Forwarded from a graph body the identity test is
False, so the builder takes its metal branch and every scf and nscf runs
``occupations='smearing', smearing='cold', degauss=0.02``. No error, no warning,
wrong physics; six months of stored calculations before anyone looked.

To be clear about what is being asked for: ``is`` cannot be made to work
through a proxy. Identity is interpreter-level, and no ``__eq__``-style
forwarding reaches it. So the wish is not "fix ``is`` on ``TaggedValue``" --
that is unpatchable on the proxy side. The wish is that a body, and anything
the body forwards a value to, receives the plain Python value, with the proxy
resolved at the boundary before third-party code ever sees it. The ``is``
comparison below is the demonstration of why a proxy escaping into code that
never opted in is unacceptable, not a defect to be patched where it shows.

Related upstream: scinode/node-graph #152 (``is`` semantics), #176 (what an
Enum-typed input should receive), #178 (membership decided twice, DRAFT PR),
#175 (``Literal`` unsupported), aiidateam/aiida-workgraph #800 (DRAFT PR).

Each ``# mwe:`` region below is one example in ``docs/index.rst`` and must
read on its own, so a definition two regions share is repeated in each,
identically; the tests bind the last copy.

NOTE: deliberately no ``from __future__ import annotations`` -- the Enum and
``Literal`` hints below are read at runtime to build the sockets.
"""

from enum import Enum
from typing import Annotated, Literal

import pytest
from aiida import orm
from aiida_workgraph import WorkGraph, namespace, task


# ----------------------------------------------------------------------
# WISH: a member should be deliverable at all
# ----------------------------------------------------------------------


# mwe: enum-member-socket
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): passing an Enum member as a "
    "socket value builds fine and dies at run with 'Cannot serialize the provided "
    "object. Type: <module>.SpinType ... not found in provided serializers'. "
    "`aiida_pythonjob.data.serializer.general_serializer` keys its registry on the "
    "exact `module.ClassName` and never walks the MRO, so no entry covers "
    "`enum.Enum` -- although `aiida.orm.to_aiida_type` already maps any member to "
    "`EnumData`. We wish an Enum member were serializable out of the box. "
    "(Escape hatch: wrap it yourself as `orm.EnumData(member)` -- see below for "
    "what that then delivers.)"
)
def test_enum_member_crosses_a_socket(aiida_profile):
    @task
    def leaf(spin):
        return str(spin)

    @task.graph
    def top(spin: SpinType):
        return leaf(spin=spin).result

    graph = top.build(spin=SpinType.COLLINEAR)
    graph.run()
    assert graph.outputs.result.value == "SpinType.COLLINEAR"


def test_enum_nested_in_a_dict_is_refused(aiida_profile):
    @task
    def leaf(cfg):
        return str(cfg["spin"])

    @task.graph
    def top(cfg: dict):
        leaf(cfg=cfg)

    with pytest.raises(Exception, match="not json-serializable"):
        top.build(cfg={"spin": SpinType.COLLINEAR}).run()


# end mwe: enum-member-socket


# ----------------------------------------------------------------------
# WISH: what ``orm.EnumData`` then delivers -- two different things
# ----------------------------------------------------------------------


# mwe: enum-graph-body
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


def third_party(spin):
    """Stand-in for library code that branches on identity, not equality."""
    return "polarized" if spin is SpinType.COLLINEAR else "unpolarized"


@task
def seen(x):
    return x


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): an `orm.EnumData` input "
    "reaches a @task.graph body as a `TaggedValue` proxy over the node, on both "
    "the eager and the deferred path. `spin == SpinType.COLLINEAR` is True (the "
    "proxy forwards __eq__) but `spin is SpinType.COLLINEAR` is False, so library "
    "code that branches on identity silently takes the wrong branch -- there is no "
    "error to see. No proxy can satisfy `is`, so the fix is not a better proxy: we "
    "wish the body received the member itself. (Escape hatch: "
    "`SpinType(getattr(spin, 'value', spin))` at every such call site.)"
)
def test_graph_body_receives_the_member(aiida_profile):
    @task.graph
    def inner(spin: SpinType):
        return seen(x=third_party(spin)).result

    @task.graph
    def top(spin: SpinType) -> Annotated[dict, namespace(equal=bool, eager=str, deferred=str)]:
        return {
            "equal": seen(x=spin == SpinType.COLLINEAR).result,
            "eager": seen(x=third_party(spin)).result,
            "deferred": inner(spin=spin).result,
        }

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))
    graph.run()
    assert graph.outputs.equal.value  # control: the proxy forwards ==
    assert (graph.outputs.eager.value, graph.outputs.deferred.value) == ("polarized", "polarized")


# end mwe: enum-graph-body


# mwe: enum-task-body
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b): the SAME `orm.EnumData` input "
    "reaches a plain @task body as the bare `str` 'collinear' -- the member's "
    "value, with the Enum class gone. So `spin == SpinType.COLLINEAR` is False "
    "here while it is True one level up in the graph body. We wish one socket "
    "delivered one type. (Escape hatch: `SpinType(getattr(spin, 'value', spin))` "
    "happens to cover both shapes, which is why it is applied blindly.)"
)
def test_task_body_receives_the_member(aiida_profile):
    @task
    def leaf(spin):
        return type(spin).__name__

    @task.graph
    def top(spin: SpinType):
        return leaf(spin=spin).result

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))
    graph.run()
    assert graph.outputs.result.value == "SpinType"


# end mwe: enum-task-body


def test_the_member_survives_to_dict_and_back(aiida_profile):
    """GUARD: the in-memory serialization keeps the member; only the run loses it.

    Worth pinning because it makes the loss invisible to the obvious test: a
    ``from_dict(to_dict())`` round-trip reports the member intact.
    """

    @task.graph
    def inner(spin: SpinType):
        return seen(x=third_party(spin)).result

    @task.graph
    def top(spin: SpinType):
        inner(spin=spin)

    data = top.build(spin=SpinType.COLLINEAR).to_dict()
    assert data["tasks"]["graph_inputs"]["inputs"]["spin"] is SpinType.COLLINEAR
    assert WorkGraph.from_dict(data).to_dict()["tasks"]["graph_inputs"]["inputs"]["spin"] is (
        SpinType.COLLINEAR
    )


# ----------------------------------------------------------------------
# The workaround we ship, as a guard -- and as an anti-pattern
# ----------------------------------------------------------------------


# mwe: enum-coerce
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


def coerce(enum_cls, value):
    """The idiom aiida-koopmans2 applies at every body that forwards an Enum."""
    return enum_cls(getattr(value, "value", value))


@task
def seen(x):
    return x


def test_the_coercion_we_apply_everywhere(aiida_profile):
    @task
    def leaf(spin):
        return coerce(SpinType, spin) is SpinType.COLLINEAR

    @task.graph
    def top(spin: SpinType) -> Annotated[dict, namespace(body=bool, leaf=bool)]:
        return {
            "body": seen(x=coerce(SpinType, spin) is SpinType.COLLINEAR).result,
            "leaf": leaf(spin=spin).result,
        }

    graph = top.build(spin=orm.EnumData(SpinType.COLLINEAR))
    graph.run()
    assert graph.outputs.body.value
    assert graph.outputs.leaf.value


# end mwe: enum-coerce


# ----------------------------------------------------------------------
# WISH: the declared Enum type should be a membership rule
# ----------------------------------------------------------------------


# mwe: enum-foreign-member
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


class Foreign(Enum):
    """A different Enum that happens to share a member value."""

    COLLINEAR = "collinear"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: a socket "
    "annotated `spin: SpinType` accepts a member of a DIFFERENT Enum whose value "
    "happens to match, at build and at run alike -- the annotation is shape, never "
    "a content rule. We wish membership were checked once, at build, by the "
    "builder alone, and the body then received the member unchanged. "
    "(No escape hatch: every route hand-writes its own refusal.)"
)
def test_foreign_member_is_rejected_at_build(aiida_profile):
    @task
    def leaf(spin):
        return spin

    @task.graph
    def top(spin: SpinType):
        leaf(spin=spin)

    with pytest.raises(Exception):
        top.build(spin=orm.EnumData(Foreign.COLLINEAR))


# end mwe: enum-foreign-member


# mwe: enum-literal
class SpinType(Enum):
    """Stands in for aiida-quantumespresso's ``SpinType``."""

    NONE = "none"
    COLLINEAR = "collinear"
    NON_COLLINEAR = "non_collinear"


@pytest.mark.xfail(
    reason="aiida-workgraph 0.9.0 (main @ 502c1b5b) / node-graph 0.6.5: narrowing a "
    "socket to two members with `Literal[SpinType.COLLINEAR, SpinType.NONE]` "
    "constrains nothing -- `_leaf_from_type` drops Literal to a `workgraph.annotated` "
    "socket carrying only `extras={'py_type': 'typing.Literal'}`, and "
    "`SpinType.NON_COLLINEAR` builds and runs (scinode/node-graph #175). This is the "
    "smallest contract we want short of a Pydantic input model: the BUILDER raises "
    "on a member outside the narrowing, and the body then gets the member unchanged, "
    "with no coercion anywhere. (No escape hatch: the route validates by hand.)"
)
def test_literal_narrowing_is_enforced_at_build(aiida_profile):
    @task
    def leaf(spin: Literal[SpinType.COLLINEAR, SpinType.NONE]):
        return spin

    @task.graph
    def top(spin):
        leaf(spin=spin)

    with pytest.raises(Exception):
        top.build(spin=orm.EnumData(SpinType.NON_COLLINEAR))


# end mwe: enum-literal
