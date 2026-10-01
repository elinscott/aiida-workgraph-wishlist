A graph cannot echo its own input (design)
==========================================

Echoing a ``dict`` input fails eagerly and works deferred
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-dict-eager
   :end-before: # end mwe: echo-dict-eager
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_echoes_input.py>`__

Echoing a ``dict`` input from a top-level build raises, while the identical graph called as a node inside another graph is accepted. The answer depends on the wrapper, not the value: an eager body's ``dict`` is walked leaf by leaf and refused, and a deferred body's ``orm.Dict`` counts as one leaf. A scalar input echoes on both paths.

See ``tests/test_graph_echoes_input.py::test_dict_input_echoes_from_an_eager_body`` (wish). Controls: ``test_dict_input_echoes_from_a_deferred_body`` and ``test_scalar_input_echoes`` (guards).

The passthrough task we ship
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_graph_echoes_input.py
   :language: python
   :start-after: # mwe: echo-passthrough
   :end-before: # end mwe: echo-passthrough
   :caption: `tests/test_graph_echoes_input.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_echoes_input.py>`__

The workaround is a ``@task`` that returns its argument unchanged. We have four of these, each a process node that did no work.

See ``tests/test_graph_echoes_input.py::test_the_passthrough_task_we_ship`` (guard).

What we want: ``return {"payload": payload}`` either works as a passthrough link, or fails the same way wherever the graph is called.

Upstream: none yet. Drafted: ``proposed-issues/12-node-graph-echo-graph-input.md``.
