Bugs
====

.. dropdown:: A leading-underscore task name fails at build (granted)

   .. literalinclude:: ../../tests/test_link_labels.py
      :language: python
      :start-after: # mwe: underscore-name
      :end-before: # end mwe: underscore-name
      :caption: `tests/test_link_labels.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_link_labels.py>`__

   A ``_hidden`` task name now fails at build with a clear message instead of silently not running. Granted by `aiida-workgraph #787 <https://github.com/aiidateam/aiida-workgraph/issues/787>`__ (closes `aiida-workgraph #784 <https://github.com/aiidateam/aiida-workgraph/issues/784>`__).

   See ``tests/test_link_labels.py::test_underscore_task_name_raises_at_build`` (guard).

The dataclass default reported as a missing input is listed in :doc:`annotated-python`, where it matters. See ``tests/test_plain_python_in_bodies.py::test_dataclass_default_is_not_a_missing_input`` (wish).
