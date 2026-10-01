A graph cannot echo its own input (design)
==========================================

Echoing a ``dict`` input fails eagerly and works deferred
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-dict-eager
   :end-before: # end mwe: echo-dict-eager
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_echoes_input.py>`__

Echoing a ``dict`` input from a top-level build raises; the identical graph called inside another graph is accepted. A scalar echoes on both paths.

The passthrough task we ship
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-passthrough
   :end-before: # end mwe: echo-passthrough
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_echoes_input.py>`__

A ``@task`` that returns its argument unchanged: a process node that did no work. We ship four.

What we want: ``return {"payload": payload}`` either works as a passthrough link, or fails the same way wherever the graph is called.

