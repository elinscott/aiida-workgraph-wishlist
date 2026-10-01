Zones versus native control flow
================================

Loop state needs ``ctx``; the natural spelling is silently wrong
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_while_zone.py
   :language: python
   :start-after: # mwe: while-zone
   :end-before: # end mwe: while-zone
   :caption: `tests/test_while_zone.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_while_zone.py>`__

Written naturally, a ``While`` loop runs to ``max_iterations`` on a frozen value and returns 2 instead of 3, exit status 0. Through ``ctx`` it works; as a recursive ``@task.graph`` it works with a ``max_depth`` ceiling and a process per layer.

What works today
~~~~~~~~~~~~~~~~

.. dropdown:: A ``for`` loop in a graph body fans out with no unpack task

   .. literalinclude:: ../../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: for-loop-fanout
      :end-before: # end mwe: for-loop-fanout
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

   ``for k, v in data.items()`` in a graph body fans out with no unpack task.

.. dropdown:: ``z.value`` is the ``Map`` entry and ``z.key`` its key

   .. literalinclude:: ../../tests/test_zone_ergonomics.py
      :language: python
      :start-after: # mwe: map-value
      :end-before: # end mwe: map-value
      :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

   ``z.value`` is now the entry and ``z.key`` its key, granted by `aiida-workgraph #792 <https://github.com/aiidateam/aiida-workgraph/issues/792>`__ (closes `aiida-workgraph #785 <https://github.com/aiidateam/aiida-workgraph/issues/785>`__). ``z.item`` remains as a deprecated alias.

What we want: write the loop you think in.

Proposal: lower ``While`` to the recursive form internally (`aiida-workgraph #738 <https://github.com/aiidateam/aiida-workgraph/issues/738>`__).

