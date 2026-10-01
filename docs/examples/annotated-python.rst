Start from annotated Python, change as little as possible (design)
==================================================================

What we want: take a function annotated with ``TypedDict`` and ``dataclass`` types, put ``@task`` or ``@task.graph`` on it, and have it work.

``None`` is a value
~~~~~~~~~~~~~~~~~~~

Issue `aiida-workgraph #779 <https://github.com/aiidateam/aiida-workgraph/issues/779>`__ · Issue `node-graph #172 <https://github.com/scinode/node-graph/issues/172>`__ · PR `node-graph #173 <https://github.com/scinode/node-graph/pull/173>`__ · PR `node-graph #174 <https://github.com/scinode/node-graph/pull/174>`__

.. dropdown:: A ``None`` field of a TypedDict is gone on the far side (wish)

   .. literalinclude:: ../../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: none-typeddict-field
      :end-before: # end mwe: none-typeddict-field
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

   A ``None``-valued ``TypedDict`` field is gone on the far side.

.. dropdown:: An explicit ``x=None`` task argument is dropped (wish)

   .. literalinclude:: ../../tests/test_none_handling.py
      :language: python
      :start-after: # mwe: none-kwarg
      :end-before: # end mwe: none-kwarg
      :caption: `tests/test_none_handling.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_none_handling.py>`__

   An explicit ``x=None`` is dropped and ``sink`` runs with its default. A ``None`` inside an opaque ``dict`` value survives.

.. dropdown:: A dataclass field left at its ``None`` default is reported missing (bug, wish)

   .. literalinclude:: ../../tests/test_plain_python_in_bodies.py
      :language: python
      :start-after: # mwe: dataclass-default
      :end-before: # end mwe: dataclass-default
      :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

   A bug, shown because it closes the ``dataclass`` escape: a field left at its ``None`` default, or passed ``None``, is reported as a missing required input.

What we want: ``None`` is a value like any other. An explicit ``None`` arrives as ``None``, and a field with a default is optional.

Granted
~~~~~~~

.. dropdown:: A dynamic-namespace graph runs under ``from __future__ import annotations`` (granted)

   .. literalinclude:: ../../tests/test_future_annotations.py
      :language: python
      :start-after: # mwe: future-annotations
      :end-before: # end mwe: future-annotations
      :caption: `tests/test_future_annotations.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_future_annotations.py>`__

   A dynamic-namespace graph now runs in a module with ``from __future__ import annotations``. Granted by `aiida-workgraph #788 <https://github.com/aiidateam/aiida-workgraph/issues/788>`__ (closes `aiida-workgraph #783 <https://github.com/aiidateam/aiida-workgraph/issues/783>`__).
