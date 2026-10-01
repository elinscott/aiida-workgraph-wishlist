Start from annotated Python, change as little as possible (design)
==================================================================

What we want: take a function annotated with TypedDicts and dataclasses, put ``@task`` or ``@task.graph`` on it, and have it work.

``None`` is a value
~~~~~~~~~~~~~~~~~~~

.. dropdown:: A ``None`` field of a TypedDict is gone on the far side (wish)

   .. literalinclude:: ../../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: none-typeddict-field
      :end-before: # end mwe: none-typeddict-field
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

   A ``None``-valued TypedDict field is gone on the far side, so a closed-shell ``tot_magnetization=None`` looks the same as one never set.

   See ``tests/test_plain_python_in_bodies.py::test_none_field_of_a_typeddict_survives`` (wish).

.. dropdown:: An explicit ``x=None`` task argument is dropped (wish)

   .. literalinclude:: ../../tests/test_none_handling.py
      :language: python
      :start-after: # mwe: none-kwarg
      :end-before: # end mwe: none-kwarg
      :caption: `tests/test_none_handling.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_none_handling.py>`__

   An explicit ``x=None`` is dropped and ``sink`` runs with its default ``"SENTINEL"``. A ``None`` inside one opaque ``dict`` value does survive, which is why we model per-step inputs as a frozen dataclass rather than the TypedDict we would write by default.

   See ``tests/test_none_handling.py::test_none_task_input_is_delivered`` (wish). Control: ``test_none_inside_opaque_dict_survives`` (guard).

.. dropdown:: A dataclass field left at its ``None`` default is reported missing (bug, wish)

   .. literalinclude:: ../../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: dataclass-default
      :end-before: # end mwe: dataclass-default
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

   A **bug**, shown here because it closes the dataclass escape: ``Settings`` declares ``tot_magnetization: Optional[float] = None``, and a field left at its default, or passed ``None``, is reported as a missing required input. On 0.9.0 the dataclass route fails too: a ``None`` field is reported as a missing required input.

   See ``tests/test_plain_python_in_bodies.py::test_dataclass_default_is_not_a_missing_input`` (wish).

What we want: ``None`` is a value like any other. An explicit ``None`` arrives as ``None``, and a field with a default is optional.

Upstream: `aiida-workgraph #779 <https://github.com/aiidateam/aiida-workgraph/issues/779>`__ (``None`` inputs). The same default-means-required shape for pydantic fields: `node-graph #172 <https://github.com/scinode/node-graph/issues/172>`__ (issue), with `node-graph #173 <https://github.com/scinode/node-graph/issues/173>`__ and `node-graph #174 <https://github.com/scinode/node-graph/issues/174>`__ (PRs, open).

Granted
~~~~~~~

.. dropdown:: A dynamic-namespace graph runs under ``from __future__ import annotations`` (granted)

   .. literalinclude:: ../../tests/test_future_annotations.py
      :language: python
      :start-after: # mwe: future-annotations
      :end-before: # end mwe: future-annotations
      :caption: `tests/test_future_annotations.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_future_annotations.py>`__

   A dynamic-namespace graph now runs in a module with ``from __future__ import annotations``. Granted by `aiida-workgraph #788 <https://github.com/aiidateam/aiida-workgraph/issues/788>`__ (closes `aiida-workgraph #783 <https://github.com/aiidateam/aiida-workgraph/issues/783>`__).

   See ``tests/test_future_annotations.py::test_dynamic_namespace_works_under_future_annotations`` (guard).
