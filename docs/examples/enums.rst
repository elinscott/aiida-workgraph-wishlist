Use Enums normally (design)
===========================

Delivery
~~~~~~~~

A bare member cannot cross a socket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-member-socket
   :end-before: # end mwe: enum-member-socket
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

A bare member builds and then dies at run. The pythonjob serializer registry keys on the exact class and never walks the MRO, though ``to_aiida_type`` already maps any member to ``EnumData``. A member inside a ``dict`` is refused at run with ``not json-serializable``, which is loud and the right answer.

See ``tests/test_enum_coercion.py::test_enum_member_crosses_a_socket`` (wish). Controls: ``test_enum_nested_in_a_dict_is_refused`` (guard) and ``tests/test_node_and_serialization.py::test_enum_coerces_to_enumdata_not_str`` (guard).

A graph body gets a proxy, so ``is`` is False
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-graph-body
   :end-before: # end mwe: enum-graph-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

Wrapped as ``orm.EnumData``, the member reaches a graph body as a proxy on both the eager and the deferred path, so ``==`` is True, which the test asserts as its control, and ``is`` is False, and ``third_party``, which tests ``spin is SpinType.COLLINEAR``, takes the wrong branch.

See ``tests/test_enum_coercion.py::test_graph_body_receives_the_member`` (wish).

A task body gets a bare ``str``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-task-body
   :end-before: # end mwe: enum-task-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

The same ``EnumData`` reaches a plain ``@task`` body as the bare ``str`` ``'collinear'``, so even ``==`` is False one level below where it was True.

See ``tests/test_enum_coercion.py::test_task_body_receives_the_member`` (wish).

The workaround we ship
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-coerce
   :end-before: # end mwe: enum-coerce
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

``coerce`` recovers the member on both paths. It has to be written at every call site, and it silently accepts a member of a different Enum with a matching value.

See ``tests/test_enum_coercion.py::test_the_coercion_we_apply_everywhere`` (guard).

Membership
~~~~~~~~~~

A member of another Enum is accepted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-foreign-member
   :end-before: # end mwe: enum-foreign-member
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

A ``spin: SpinType`` socket is a generic ``workgraph.annotated`` socket: ``Foreign.COLLINEAR`` builds and runs, and the leaf receives the ``str`` ``'collinear'``. Even ``orm.Int(3)`` builds.

See ``tests/test_enum_coercion.py::test_foreign_member_is_rejected_at_build`` (wish).

``Literal`` narrowing constrains nothing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-literal
   :end-before: # end mwe: enum-literal
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

``Literal[SpinType.COLLINEAR, SpinType.NONE]`` constrains nothing: node-graph drops the ``Literal`` to an untyped annotated socket.

See ``tests/test_enum_coercion.py::test_literal_narrowing_is_enforced_at_build`` (wish).

What we want: the member goes in and the member comes out, on every path.

Upstream plugins spell modes as Enums (``SpinType.COLLINEAR``, ``ElectronicType.INSULATOR``), so a workflow wrapping them has to carry members down to their builders. Today there is no path on which you write the member and read the member back. What it cost: aiida-quantumespresso's ``get_builder_from_protocol`` branches on ``electronic_type is ElectronicType.INSULATOR``. Forwarded from a graph body that test was False, so every scf and nscf ran with cold smearing. No error, no warning, six months of wrong calculations.

``is`` cannot be fixed on a proxy. Identity is decided by the interpreter and no forwarding reaches it. So the ask is not a better proxy; it is that the plain value is delivered, with the proxy resolved at the boundary before any third-party code sees it.

Two ways to get there
~~~~~~~~~~~~~~~~~~~~~

1. **Minimal, builder-side.** An Enum socket may be declared as a subset of members (``Literal[SpinType.COLLINEAR, SpinType.NONE]``). The builder alone checks membership, once, and refuses the build on a mismatch. The body then receives the member unchanged, and nothing else coerces. This is the smallest contract I would ask for, and on its own it would retire our ``coerce`` calls and every hand-written route refusal of a spin mode.
2. **Pydantic** ``input_model``. A task's inputs are a pydantic model, validated at build (`node-graph #182 <https://github.com/scinode/node-graph/issues/182>`__ and `aiida-workgraph #814 <https://github.com/aiidateam/aiida-workgraph/issues/814>`__, both draft PRs). It gives richer rules (field validators, cross-field checks) and build-time errors in the model's words. I am hesitant to recommend a full pivot if the contract in option 1 can be had; the question for the group is whether 1 is a subset of 2 or a separate path.

Upstream: `node-graph #152 <https://github.com/scinode/node-graph/issues/152>`__ (``is`` semantics), `node-graph #175 <https://github.com/scinode/node-graph/issues/175>`__ (``Literal`` unsupported), `node-graph #176 <https://github.com/scinode/node-graph/issues/176>`__ (what an Enum-typed input should receive), `node-graph #178 <https://github.com/scinode/node-graph/issues/178>`__ (draft PR, membership decided twice on two representations) with `aiida-workgraph #800 <https://github.com/aiidateam/aiida-workgraph/issues/800>`__ (draft PR). Delivery is drafted but not filed: ``proposed-issues/11-aiida-workgraph-enum-delivery.md``.
