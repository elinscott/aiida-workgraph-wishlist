aiida-workgraph wishlist
========================

*Meeting notes, 2026-10-02.*

Every item below is a test in ``tests/``. A passing test is a **guard**: it pins behaviour that works today, often with the workaround we ship written into it. An ``xfail`` test is a **wish**: ``xfail_strict`` is on, so the day a wish is granted the suite fails loudly and we promote it to a guard.

Each item opens with a complete example, included from its test file and linked to it; the test's assertions, and for a wish its ``xfail`` reason, say what happens today. The test name comes last.

Unless a line says otherwise, statuses are as the tests' reason strings record them: aiida-workgraph 0.9.0 (main @ 502c1b5), node-graph 0.6.5. Two modules still cite 0.8.1 in their reason strings; those lines say so.

47 tests: 30 guards, 17 wishes. Each is sorted into one of three kinds:

- **Design rethink**: the framework's model gets in the way of plain Python. These need the group.
- **Feature request**: a missing capability with an obvious shape.
- **Bug**: behaviour nobody intended. Listed at the end for completeness.

The first three sections are the three things I want most. The rest follow from big to small.

Every example assumes its module's imports. Across the suite they are:

.. code-block:: python

   import json
   from dataclasses import dataclass
   from enum import Enum
   from typing import Annotated, Literal, Optional, TypedDict

   import pytest
   from aiida import orm
   from aiida.orm import Int
   from aiida_workgraph import Map, While, WorkGraph, dynamic, get_current_graph, namespace, task

Six modules also open with ``from __future__ import annotations``: ``test_future_annotations.py``, ``test_graph_body_values.py``, ``test_link_labels.py``, ``test_node_and_serialization.py``, ``test_none_handling.py`` and ``test_while_zone.py``. The others leave it out on purpose, because their hints are read at runtime.

Tests take the suite's ``aiida_profile`` fixture, a throwaway profile, or its ``collect`` fixture, which builds and runs a zero-argument graph and returns the stored result dicts carrying a given ``_tag``. Tests that call ``.run()`` themselves read results back with ``_tagged``:

.. literalinclude:: ../tests/test_plain_python_in_bodies.py
   :language: python
   :pyobject: _tagged

An example that needs a class another example also uses repeats it, so each example reads on its own.

1. Start from annotated Python, change as little as possible (design)
----------------------------------------------------------------------

What we want: take a function annotated with TypedDicts and dataclasses, put ``@task`` or ``@task.graph`` on it, and have it work.

``None`` is a value
~~~~~~~~~~~~~~~~~~~

.. dropdown:: A ``None`` field of a TypedDict is gone on the far side (wish)

   .. literalinclude:: ../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: none-typeddict-field
      :end-before: # end mwe: none-typeddict-field
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_plain_python_in_bodies.py>`__

   A ``None``-valued TypedDict field is gone on the far side, so a closed-shell ``tot_magnetization=None`` looks the same as one never set.

   See ``tests/test_plain_python_in_bodies.py::test_none_field_of_a_typeddict_survives`` (wish).

.. dropdown:: An explicit ``x=None`` task argument is dropped (wish)

   .. literalinclude:: ../tests/test_none_handling.py
      :language: python
      :start-after: # mwe: none-kwarg
      :end-before: # end mwe: none-kwarg
      :caption: `tests/test_none_handling.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_none_handling.py>`__

   An explicit ``x=None`` is dropped and ``sink`` runs with its default ``"SENTINEL"``. A ``None`` inside one opaque ``dict`` value does survive, which is why we model per-step inputs as a frozen dataclass rather than the TypedDict we would write by default.

   See ``tests/test_none_handling.py::test_none_task_input_is_delivered`` (wish, reason cites 0.8.1). Control: ``test_none_inside_opaque_dict_survives`` (guard).

.. dropdown:: A dataclass field left at its ``None`` default is reported missing (bug, wish)

   .. literalinclude:: ../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: dataclass-default
      :end-before: # end mwe: dataclass-default
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_plain_python_in_bodies.py>`__

   A **bug**, shown here because it closes the dataclass escape: ``Settings`` declares ``tot_magnetization: Optional[float] = None``, and a field left at its default, or passed ``None``, is reported as a missing required input.

   See ``tests/test_plain_python_in_bodies.py::test_dataclass_default_is_not_a_missing_input`` (wish).

What we want: ``None`` is a value like any other. An explicit ``None`` arrives as ``None``, and a field with a default is optional.

Upstream: `aiida-workgraph #779 <https://github.com/aiidateam/aiida-workgraph/issues/779>`__ (``None`` inputs). The same default-means-required shape for pydantic fields: `node-graph #172 <https://github.com/scinode/node-graph/issues/172>`__ (issue), with `node-graph #173 <https://github.com/scinode/node-graph/issues/173>`__ and `node-graph #174 <https://github.com/scinode/node-graph/issues/174>`__ (PRs, open).

Granted
~~~~~~~

.. dropdown:: A dynamic-namespace graph runs under ``from __future__ import annotations`` (granted)

   .. literalinclude:: ../tests/test_future_annotations.py
      :language: python
      :start-after: # mwe: future-annotations
      :end-before: # end mwe: future-annotations
      :caption: `tests/test_future_annotations.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_future_annotations.py>`__

   A dynamic-namespace graph now runs in a module with ``from __future__ import annotations``. Granted by `aiida-workgraph #788 <https://github.com/aiidateam/aiida-workgraph/issues/788>`__ (closes `aiida-workgraph #783 <https://github.com/aiidateam/aiida-workgraph/issues/783>`__).

   See ``tests/test_future_annotations.py::test_dynamic_namespace_works_under_future_annotations`` (guard).

2. No ORM objects floating around (design)
-------------------------------------------

``int`` is an ``int``, ``dict`` is a ``dict``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A dataclass ``int`` field is an ``orm.Int`` in a graph body
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: int-field
   :end-before: # end mwe: int-field
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_plain_python_in_bodies.py>`__

In a ``@task.graph`` body a dataclass ``int`` field is a proxy over ``orm.Int``. A ``@task`` body gets a real ``int`` from the same socket.

See ``tests/test_plain_python_in_bodies.py::test_graph_body_int_field_is_an_int`` (wish). Control: ``test_task_body_rebuilds_the_dataclass`` (guard).

A ``dict`` input is a ``dict`` eagerly and an ``orm.Dict`` deferred
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: dict-input
   :end-before: # end mwe: dict-input
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_plain_python_in_bodies.py>`__

A ``dict`` input is a proxy over ``dict`` when the body runs eagerly and over ``orm.Dict`` when deferred, so ``isinstance(d, dict)`` gives two answers for one line of code.

See ``tests/test_plain_python_in_bodies.py::test_dict_input_is_the_same_on_both_paths`` (wish).

A scalar input needs ``.value``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_node_and_serialization.py
   :language: python
   :start-after: # mwe: scalar-dot-value
   :end-before: # end mwe: scalar-dot-value
   :caption: `tests/test_node_and_serialization.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_node_and_serialization.py>`__

A scalar graph input is a proxy over ``orm.Str``, so you reach through ``.value``, while a ``dict`` input in the same place subscripts directly. A node that leaks further bites again: ``str(orm.Str("hello"))`` is a ``uuid: ...`` repr, which once landed in a QueryBuilder filter.

See ``tests/test_node_and_serialization.py::test_scalar_input_in_graph_body_needs_dot_value`` and ``test_str_of_node_is_repr_not_value`` (guards).

What already works in a deferred body
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Subscript, ``if`` and ``is None`` see the concrete value in a deferred body (guards)

   .. literalinclude:: ../tests/test_graph_body_values.py
      :language: python
      :start-after: # mwe: deferred-body-values
      :end-before: # end mwe: deferred-body-values
      :caption: `tests/test_graph_body_values.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_graph_body_values.py>`__

   Subscript, a real ``if`` on the subscripted value, and ``x is None`` all see the concrete per-invocation value. ``is None`` works because ``None`` arrives unwrapped.

   See ``tests/test_graph_body_values.py::test_subscript_in_deferred_body_resolves``, ``test_structural_branch_in_deferred_body`` and ``test_is_none_works_in_deferred_body`` (guards).

Nodes a body needs whole
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: file-node
   :end-before: # end mwe: file-node
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_plain_python_in_bodies.py>`__

A stored ``SinglefileData`` cannot reach a plain ``@task``. Only ``@task.calcfunction`` receives the node, at the cost of a process node and provenance for work that is not a calculation. Other nodes arrive unwrapped: a ``StructureData`` reaches a ``@task`` body as ``ase.Atoms``, and returning an already-stored node needs ``@task.workfunction``.

See ``tests/test_plain_python_in_bodies.py::test_plain_task_can_take_a_file_node`` (wish). Controls: ``test_calcfunction_is_the_only_way_to_a_file_node`` (guard), and ``tests/test_node_and_serialization.py::test_task_body_receives_deserialized_payload`` and ``test_workfunction_needed_to_emit_an_existing_node`` (guards).

What we want: a body sees the Python types its signature declares on every path (eager, deferred, restored from a checkpoint), and can ask for the node instead of its value. Serialization is the framework's concern.

Upstream: `aiida-workgraph #780 <https://github.com/aiidateam/aiida-workgraph/issues/780>`__ (scalars promoted to ``orm`` types at a graph boundary), `aiida-workgraph #786 <https://github.com/aiidateam/aiida-workgraph/issues/786>`__ (scalar needs ``.value``, dict does not), `aiida-pythonjob #78 <https://github.com/aiidateam/aiida-pythonjob/issues/78>`__ and `aiida-pythonjob #83 <https://github.com/aiidateam/aiida-pythonjob/issues/83>`__ (a node into a body), `node-graph #177 <https://github.com/scinode/node-graph/issues/177>`__ (PR, proxy masquerades as an iterable). The umbrella is drafted but not filed: ``proposed-issues/13-aiida-workgraph-body-delivery-contract.md``.

3. Use Enums normally (design)
------------------------------

Delivery
~~~~~~~~

A bare member cannot cross a socket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-member-socket
   :end-before: # end mwe: enum-member-socket
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

A bare member builds and then dies at run. The pythonjob serializer registry keys on the exact class and never walks the MRO, though ``to_aiida_type`` already maps any member to ``EnumData``. A member inside a ``dict`` is refused at run with ``not json-serializable``, which is loud and the right answer.

See ``tests/test_enum_coercion.py::test_enum_member_crosses_a_socket`` (wish). Controls: ``test_enum_nested_in_a_dict_is_refused`` (guard) and ``tests/test_node_and_serialization.py::test_enum_coerces_to_enumdata_not_str`` (guard).

A graph body gets a proxy, so ``is`` is False
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-graph-body
   :end-before: # end mwe: enum-graph-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

Wrapped as ``orm.EnumData``, the member reaches a graph body as a proxy, so ``==`` is True and ``is`` is False, and ``third_party``, which tests ``spin is SpinType.COLLINEAR``, takes the wrong branch. An older test makes the same point with ``block["kind"] is Kind.A``, but its ``make_block`` returns the plain string ``"a"``, so that ``is`` would be False with no proxy at all, and its ``==`` twin passes only because ``Kind`` subclasses ``str``.

See ``tests/test_enum_coercion.py::test_graph_body_receives_the_member`` (wish). Older: ``tests/test_graph_body_values.py::test_is_against_enum_in_deferred_body`` (wish, reason cites 0.8.1) and ``test_eq_against_enum_in_deferred_body`` (guard).

A task body gets a bare ``str``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-task-body
   :end-before: # end mwe: enum-task-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

The same ``EnumData`` reaches a plain ``@task`` body as the bare ``str`` ``'collinear'``, so even ``==`` is False one level below where it was True.

See ``tests/test_enum_coercion.py::test_task_body_receives_the_member`` (wish).

The workaround we ship
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-coerce
   :end-before: # end mwe: enum-coerce
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

``coerce`` recovers the member on both paths. It has to be written at every call site, and it silently accepts a member of a different Enum with a matching value.

See ``tests/test_enum_coercion.py::test_the_coercion_we_apply_everywhere`` (guard).

Membership
~~~~~~~~~~

A member of another Enum is accepted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-foreign-member
   :end-before: # end mwe: enum-foreign-member
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

A ``spin: SpinType`` socket accepts ``Foreign.COLLINEAR``, a member of another Enum with the same value. The annotation is shape, never a rule.

See ``tests/test_enum_coercion.py::test_foreign_member_is_rejected_at_build`` (wish).

``Literal`` narrowing constrains nothing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-literal
   :end-before: # end mwe: enum-literal
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_enum_coercion.py>`__

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

4. A graph cannot echo its own input (design)
---------------------------------------------

Echoing a ``dict`` input fails eagerly and works deferred
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-dict-eager
   :end-before: # end mwe: echo-dict-eager
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_graph_echoes_input.py>`__

Echoing a ``dict`` input from a top-level build raises, while the identical graph called as a node inside another graph is accepted. The answer depends on the wrapper, not the value: an eager body's ``dict`` is walked leaf by leaf and refused, and a deferred body's ``orm.Dict`` counts as one leaf. A scalar input echoes on both paths.

See ``tests/test_graph_echoes_input.py::test_dict_input_echoes_from_an_eager_body`` (wish). Controls: ``test_dict_input_echoes_from_a_deferred_body`` and ``test_scalar_input_echoes`` (guards).

The passthrough task we ship
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-passthrough
   :end-before: # end mwe: echo-passthrough
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_graph_echoes_input.py>`__

The workaround is a ``@task`` that returns its argument unchanged. We have four of these, each a process node that did no work.

See ``tests/test_graph_echoes_input.py::test_the_passthrough_task_we_ship`` (guard).

What we want: ``return {"payload": payload}`` either works as a passthrough link, or fails the same way wherever the graph is called.

Upstream: none yet. Drafted: ``proposed-issues/12-node-graph-echo-graph-input.md``.

5. The serialization you can test is not the one that runs (design)
--------------------------------------------------------------------

``to_dict()`` returns live objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: to-dict-live
   :end-before: # end mwe: to-dict-live
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_two_serialization_paths.py>`__

The input comes back as the same object, and the whole dict is not JSON-encodable. So ``from_dict(to_dict())`` hands an Enum member back intact, which hides the loss in section 3 from the obvious test.

See ``tests/test_two_serialization_paths.py::test_to_dict_returns_live_objects`` (guard). Also ``tests/test_enum_coercion.py::test_the_member_survives_to_dict_and_back`` (guard).

A graph that round-trips can still die at run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: round-trip-runs
   :end-before: # end mwe: round-trip-runs
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_two_serialization_paths.py>`__

A graph passes the round-trip and then dies at run. The reverse also happened: a fan-out into a typed dynamic input once passed the round-trip and died on the daemon with ``Missing in source: []. Missing in target: []``. It does not reproduce on this version and is pinned as the shape that broke; the empty-list message still deserves to name the child that mismatched.

See ``tests/test_two_serialization_paths.py::test_a_graph_that_round_trips_also_runs`` (wish). Also ``test_typed_dynamic_namespace_round_trips_and_runs`` (guard).

The daemon's checkpoint path, driven in-process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: checkpoint-path
   :end-before: # end mwe: checkpoint-path
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_two_serialization_paths.py>`__

The daemon's checkpoint path can be driven in-process, but only by assembling four undocumented pieces: ``instantiate_process``, ``AiiDAPersister``, ``get_object_loader`` and ``Bundle.unbundle``.

See ``tests/test_two_serialization_paths.py::test_the_checkpoint_path_can_be_driven_without_a_daemon`` (guard).

What we want: one serialization path a test can exercise, or a supported "encode this graph the way the engine will" check. ``to_dict()`` returns live objects, so ``from_dict(to_dict())``, the guard we run over every graph shape, never touches an encoder the engine uses.

Upstream: none yet. Drafted: ``proposed-issues/14-aiida-workgraph-two-serialization-paths.md``.

6. Zones versus native control flow (design)
--------------------------------------------

A do-while needs an unrolled first pass, ``ctx`` and a wait edge
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_while_zone.py
   :language: python
   :start-after: # mwe: while-zone
   :end-before: # end mwe: while-zone
   :caption: `tests/test_while_zone.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_while_zone.py>`__

A do-while works only with the first iteration unrolled, state plumbed through ``ctx``, and a manual wait edge. The same loop as a recursive ``@task.graph`` needs none of that, but has a ``max_depth`` ceiling and a nested process per layer.

See ``tests/test_while_zone.py::test_do_while_today_needs_unroll_ctx_and_wait_edges`` (guard). Also ``test_same_loop_via_recursion_is_clean_but_has_costs`` (guard).

What works today
~~~~~~~~~~~~~~~~

.. dropdown:: A ``for`` loop in a graph body fans out with no unpack task (guard)

   .. literalinclude:: ../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: for-loop-fanout
      :end-before: # end mwe: for-loop-fanout
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_zone_ergonomics.py>`__

   ``for k, v in data.items()`` in a graph body subscripts inline with no unpack task. This is the answer to most ``Map`` use.

   See ``tests/test_zone_ergonomics.py::test_dynamic_fanout_via_for_loop_is_clean`` (guard).

.. dropdown:: ``z.value`` is the ``Map`` entry and ``z.key`` its key (granted)

   .. literalinclude:: ../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: map-value
      :end-before: # end mwe: map-value
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_zone_ergonomics.py>`__

   ``z.value`` is now the entry and ``z.key`` its key, granted by `aiida-workgraph #792 <https://github.com/aiidateam/aiida-workgraph/issues/792>`__ (closes `aiida-workgraph #785 <https://github.com/aiidateam/aiida-workgraph/issues/785>`__). ``z.item`` remains as a deprecated alias.

   See ``tests/test_zone_ergonomics.py::test_map_value_is_the_item`` (guard).

What we want: users write the loop they think in and get the provenance of recursion. The ``for`` loop inside a ``@task.graph`` is already the clean fan-out; the ``While`` zone is where the tax is.

The proposal: lower the ``While`` zone to the recursive form internally, with the condition checked after the body. Posted as a comment on `aiida-workgraph #738 <https://github.com/aiidateam/aiida-workgraph/issues/738>`__, unanswered. The "natural" ``with While(x < 3): x = inc(x=x)`` is not in the suite: without ``ctx`` it ignores ``max_iterations`` and hangs.

Not covered by a test: which tasks in a graph are steps and which are bookkeeping, for dumping. No MWE exists yet, so it is left out here.

7. Feature requests
-------------------

A TypedDict return annotation builds the same sockets as ``namespace(...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: typeddict-return
   :end-before: # end mwe: typeddict-return
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_dynamic_namespace_typing.py>`__

A TypedDict return annotation yields an opaque ``workgraph.dict``, so a downstream namespace consumer cannot link to ``out``. The same shape spelled ``-> Annotated[dict, namespace(out=dynamic(namespace(a=int)))]`` links fine, so this is a parity gap, not a limit.

See ``tests/test_dynamic_namespace_typing.py::test_typeddict_return_annotation_is_consumable`` (wish). Control: ``test_explicit_namespace_gather_is_consumable`` (guard).

What we want: a TypedDict should build the same sockets as the explicit ``namespace(...)`` spelling.

Upstream: `node-graph #154 <https://github.com/scinode/node-graph/issues/154>`__ (issue) and `node-graph #159 <https://github.com/scinode/node-graph/issues/159>`__ (PR, open). The survey expects this may already pass on current node-graph main; the reason string records it failing at 502c1b5.

Subscript a future the way you can multiply one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_zone_ergonomics.py
   :language: python
   :start-after: # mwe: map-destructure
   :end-before: # end mwe: map-destructure
   :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_zone_ergonomics.py>`__

Destructuring a ``Map`` entry needs an unpack task with one output per field, while ``n * 2`` and ``n // 2`` on the same kind of future build ``op_mul`` and ``op_floordiv`` tasks. The refusal is at least loud, which is the model for every other proxy edge.

See ``tests/test_zone_ergonomics.py::test_destructure_map_item_without_unpack_task`` (wish). Controls: ``test_socket_arithmetic_builds_operator_tasks`` and ``test_eager_subscript_of_future_raises_loudly`` (guards).

What we want: ``socket["k"]`` builds an operator task, as ``socket * 2`` already does.

Upstream: `node-graph #156 <https://github.com/scinode/node-graph/issues/156>`__ (issue) and `node-graph #160 <https://github.com/scinode/node-graph/issues/160>`__ (PR, open; carried on our fork as ``op_getitem``). Residue once granted: `node-graph #161 <https://github.com/scinode/node-graph/issues/161>`__, operator tasks discard type information.

Re-scatter a gathered namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: rescatter
   :end-before: # end mwe: rescatter
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_dynamic_namespace_typing.py>`__

Iterating a fan-out's gathered output fails, so results cannot fan out again.

See ``tests/test_dynamic_namespace_typing.py::test_gather_then_rescatter`` (wish).

What we want: a dynamic-namespace task output can be iterated in a graph body, as a dynamic-namespace graph input already can.

Upstream: `node-graph #155 <https://github.com/scinode/node-graph/issues/155>`__.

8. Bugs
-------

.. dropdown:: A leading-underscore task name fails at build (granted)

   .. literalinclude:: ../tests/test_link_labels.py
      :language: python
      :start-after: # mwe: underscore-name
      :end-before: # end mwe: underscore-name
      :caption: `tests/test_link_labels.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/main/tests/test_link_labels.py>`__

   A ``_hidden`` task name now fails at build with a clear message instead of silently not running. Granted by `aiida-workgraph #787 <https://github.com/aiidateam/aiida-workgraph/issues/787>`__ (closes `aiida-workgraph #784 <https://github.com/aiidateam/aiida-workgraph/issues/784>`__).

   See ``tests/test_link_labels.py::test_underscore_task_name_raises_at_build`` (guard).

The dataclass default reported as a missing input is listed in section 1, where it matters. See ``tests/test_plain_python_in_bodies.py::test_dataclass_default_is_not_a_missing_input`` (wish).

How to run
----------

.. code-block:: text

   uv sync
   uv run pytest -q
   uv run pytest -rX

The last command lists the open wishes. The suite uses its own config under ``~/.aiida-wishlist`` and a throwaway profile, so it never touches a real AiiDA profile.

This page builds with:

.. code-block:: text

   uv run --group docs sphinx-build -W -b html docs docs/_build/html

aiida-core is pinned to v2.9.1: aiida-core main has absorbed plumpy, while aiida-workgraph main still imports plumpy without declaring it.
