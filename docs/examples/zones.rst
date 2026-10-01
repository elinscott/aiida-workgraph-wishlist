Zones versus native control flow (design)
=========================================

Loop state needs ``ctx``; the natural spelling is silently wrong
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_while_zone.py
   :language: python
   :start-after: # mwe: while-zone
   :end-before: # end mwe: while-zone
   :caption: `tests/test_while_zone.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_while_zone.py>`__

A ``While`` loop works only with its state plumbed through ``ctx``. Written naturally, it runs to ``max_iterations`` on a frozen value and returns 2 instead of 3 with exit status 0. The unrolled first pass and the manual wait edge are not needed on 0.9.0. The same loop as a recursive ``@task.graph`` needs none of that, but has a ``max_depth`` ceiling and a nested process per layer.

See ``tests/test_while_zone.py::test_while_loop_state_needs_ctx`` (guard). Also ``test_same_loop_via_recursion_is_clean_but_has_costs`` (guard).

What works today
~~~~~~~~~~~~~~~~

.. dropdown:: A ``for`` loop in a graph body fans out with no unpack task (guard)

   .. literalinclude:: ../../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: for-loop-fanout
      :end-before: # end mwe: for-loop-fanout
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

   ``for k, v in data.items()`` in a graph body subscripts inline with no unpack task. This is the answer to most ``Map`` use.

   See ``tests/test_zone_ergonomics.py::test_dynamic_fanout_via_for_loop_is_clean`` (guard).

.. dropdown:: ``z.value`` is the ``Map`` entry and ``z.key`` its key (granted)

   .. literalinclude:: ../../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: map-value
      :end-before: # end mwe: map-value
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

   ``z.value`` is now the entry and ``z.key`` its key, granted by `aiida-workgraph #792 <https://github.com/aiidateam/aiida-workgraph/issues/792>`__ (closes `aiida-workgraph #785 <https://github.com/aiidateam/aiida-workgraph/issues/785>`__). ``z.item`` remains as a deprecated alias.

   See ``tests/test_zone_ergonomics.py::test_map_value_is_the_item`` (guard).

What we want: users write the loop they think in and get the provenance of recursion. The ``for`` loop inside a ``@task.graph`` is already the clean fan-out; the ``While`` zone is where the tax is.

The proposal: lower the ``While`` zone to the recursive form internally, with the condition checked after the body. Posted as a comment on `aiida-workgraph #738 <https://github.com/aiidateam/aiida-workgraph/issues/738>`__, unanswered. The "natural" ``with While(x < 3): x = inc(x=x)`` is in the suite: it stops at ``max_iterations`` and returns a wrong value with exit status 0.

Not covered by a test: which tasks in a graph are steps and which are bookkeeping, for dumping. No MWE exists yet, so it is left out here.
