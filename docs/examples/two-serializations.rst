The serialization you can test is not the one that runs
=======================================================

``to_dict()`` returns live objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: to-dict-live
   :end-before: # end mwe: to-dict-live
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

The input comes back as the same object, so the dict is JSON-encodable only when every input is; with the ``Enum`` member in it, ``json.dumps`` raises ``TypeError``.

A graph that round-trips can still die at run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: round-trip-runs
   :end-before: # end mwe: round-trip-runs
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

A graph passes the round-trip and then dies at run; ``to_engine_inputs()``, which ``run()`` calls, catches it at build.

The daemon's checkpoint path, driven in-process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: checkpoint-path
   :end-before: # end mwe: checkpoint-path
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

The daemon's checkpoint path can be driven in-process, from four undocumented pieces.

What we want: one serialization, the engine's, reachable from a test.

