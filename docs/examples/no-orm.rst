No ORM objects floating around (design)
=======================================

``int`` is an ``int``, ``dict`` is a ``dict``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A dataclass ``int`` field is an ``orm.Int`` in a graph body
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: int-field
   :end-before: # end mwe: int-field
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

In a ``@task.graph`` body that runs deferred, a dataclass ``int`` field is a proxy over ``orm.Int``; run eagerly it is a plain ``int`` under the proxy. A ``@task`` body gets a real ``int`` from the same socket.

See ``tests/test_plain_python_in_bodies.py::test_graph_body_int_field_is_an_int`` (wish). Control: ``test_task_body_rebuilds_the_dataclass`` (guard).

A ``dict`` input is a ``dict`` eagerly and an ``orm.Dict`` deferred
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: dict-input
   :end-before: # end mwe: dict-input
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

A ``dict`` input is a proxy over ``dict`` when the body runs eagerly and over ``orm.Dict`` when deferred, so ``isinstance(d, dict)`` gives two answers for one line of code.

See ``tests/test_plain_python_in_bodies.py::test_dict_input_is_the_same_on_both_paths`` (wish).

A scalar input needs ``.value``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_node_and_serialization.py
   :language: python
   :start-after: # mwe: scalar-dot-value
   :end-before: # end mwe: scalar-dot-value
   :caption: `tests/test_node_and_serialization.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_node_and_serialization.py>`__

In a deferred body a scalar input is a proxy over ``orm.Str``, so you reach through ``.value``; in an eager body it is a proxy over a plain ``str``, ``int(label)`` works and ``label.value`` raises ``AttributeError``.

See ``tests/test_node_and_serialization.py::test_scalar_input_in_graph_body_needs_dot_value`` and ``test_str_of_node_is_repr_not_value`` (guards).

What already works in a deferred body
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Subscript, ``if`` and ``is None`` see the concrete value in a deferred body (guards)

   .. literalinclude:: ../../tests/test_graph_body_values.py
      :language: python
      :start-after: # mwe: deferred-body-values
      :end-before: # end mwe: deferred-body-values
      :caption: `tests/test_graph_body_values.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_body_values.py>`__

   Subscripting the deferred ``orm.Dict`` proxy returns plain Python values (``int``, ``str``, ``None``), so ``==``, ``if`` and ``is None`` compare real values.

   See ``tests/test_graph_body_values.py::test_subscript_in_deferred_body_resolves``, ``test_structural_branch_in_deferred_body`` and ``test_is_none_works_in_deferred_body`` (guards).

Nodes a body needs whole
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: file-node
   :end-before: # end mwe: file-node
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

A ``SinglefileData`` reaches a plain ``@task`` only if a deserializer for it is registered profile-wide in ``pythonjob.json``; ``@task`` has no per-task option, so per task only ``@task.calcfunction`` receives the node, at the cost of a process node and provenance for work that is not a calculation. Other nodes arrive unwrapped: a ``StructureData`` reaches a ``@task`` body as ``ase.Atoms``, and returning an already-stored node needs ``@task.workfunction``.

See ``tests/test_plain_python_in_bodies.py::test_plain_task_can_take_a_file_node`` (wish). Controls: ``test_calcfunction_receives_a_file_node`` (guard), and ``tests/test_node_and_serialization.py::test_task_body_receives_deserialized_payload`` and ``test_workfunction_needed_to_emit_an_existing_node`` (guards).

What we want: a body sees the Python types its signature declares on every path (eager, deferred, restored from a checkpoint), and can ask for the node instead of its value. Serialization is the framework's concern.

Upstream: `aiida-workgraph #780 <https://github.com/aiidateam/aiida-workgraph/issues/780>`__ (scalars promoted to ``orm`` types at a graph boundary), `aiida-workgraph #786 <https://github.com/aiidateam/aiida-workgraph/issues/786>`__ (scalar needs ``.value``, dict does not), `aiida-pythonjob #78 <https://github.com/aiidateam/aiida-pythonjob/issues/78>`__ and `aiida-pythonjob #83 <https://github.com/aiidateam/aiida-pythonjob/issues/83>`__ (a node into a body), `node-graph #177 <https://github.com/scinode/node-graph/issues/177>`__ (PR, proxy masquerades as an iterable). The umbrella is drafted but not filed: ``proposed-issues/13-aiida-workgraph-body-delivery-contract.md``.

In the wild
~~~~~~~~~~~

Five of these coercions are not hypothetical; aiida-koopmans carries them at the call sites below.

- Recovering an Enum member from a proxy or its bare value: `workgraphs/__init__.py#L35 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/__init__.py#L35>`__.
- Rebuilding a namelist override by iterating ``.items()`` rather than trusting ``dict(proxy)``: `workgraphs/dfpt.py#L293 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/dfpt.py#L293>`__.
- Unwrapping a proxied flag to a plain ``bool`` before it is stored: `workgraphs/dfpt.py#L725 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/dfpt.py#L725>`__.
- Coercing a proxied numeric field to ``int``/``float`` before arithmetic: `workgraphs/auto_wannierize.py#L203 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/auto_wannierize.py#L203>`__.
- Rebuilding a parallelization entry into a plain ``dict`` before it reaches a namespace socket: `parallelization.py#L254 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/parallelization.py#L254>`__.
