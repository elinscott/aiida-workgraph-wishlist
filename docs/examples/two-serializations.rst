The serialization you can test is not the one that runs (design)
================================================================

``to_dict()`` returns live objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: to-dict-live
   :end-before: # end mwe: to-dict-live
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

The input comes back as the same object, so the dict is JSON-encodable only when every input is; with the Enum member in it, ``json.dumps`` raises ``TypeError``.

See ``tests/test_two_serialization_paths.py::test_to_dict_returns_live_objects`` (guard). Also ``tests/test_enum_coercion.py::test_the_member_survives_to_dict_and_back`` (guard).

A graph that round-trips can still die at run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: round-trip-runs
   :end-before: # end mwe: round-trip-runs
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

A graph passes the round-trip and then dies at run. The reverse also happened: a fan-out into a typed dynamic input once passed the round-trip and died on the daemon with ``Missing in source: []. Missing in target: []``. It does not reproduce on this version and is pinned as the shape that broke; the empty-list message still deserves to name the child that mismatched. ``to_engine_inputs()``, which ``run()`` calls, raises the same error at build.

See ``tests/test_two_serialization_paths.py::test_engine_inputs_catch_what_the_round_trip_misses`` (guard).

The daemon's checkpoint path, driven in-process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_two_serialization_paths.py
   :language: python
   :start-after: # mwe: checkpoint-path
   :end-before: # end mwe: checkpoint-path
   :caption: `tests/test_two_serialization_paths.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_two_serialization_paths.py>`__

The daemon's checkpoint path can be driven in-process, but only by assembling four undocumented pieces: ``instantiate_process``, ``AiiDAPersister``, ``get_object_loader`` and ``Bundle.unbundle``.

See ``tests/test_two_serialization_paths.py::test_the_checkpoint_path_can_be_driven_without_a_daemon`` (guard).

What we want: the round-trip every graph shape gets to be the engine's serialization. The documented ``to_engine_inputs()`` already is, but ``to_dict()`` defaults to live objects and nothing points a test author at it.

Upstream: none yet. Drafted: ``proposed-issues/14-aiida-workgraph-two-serialization-paths.md``.
