No ORM objects floating around
==============================

``int`` is an ``int``, ``dict`` is a ``dict``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``dataclass`` ``int`` field is an ``orm.Int`` in a graph body
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue** `aiida-workgraph #780 <https://github.com/aiidateam/aiida-workgraph/issues/780>`__

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: int-field
   :end-before: # end mwe: int-field
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

In a ``@task.graph`` body that runs deferred, a ``dataclass`` ``int`` field is a proxy over ``orm.Int``; run eagerly it is a plain ``int`` under the proxy. A ``@task`` body gets a real ``int`` from the same socket.

A ``dict`` input is a ``dict`` eagerly and an ``orm.Dict`` deferred
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**PR** `node-graph #177 <https://github.com/scinode/node-graph/pull/177>`__

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: dict-input
   :end-before: # end mwe: dict-input
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

A ``dict`` input is a proxy over ``dict`` when the body runs eagerly and over ``orm.Dict`` when deferred, so ``isinstance(d, dict)`` gives two answers for one line of code.

A scalar input needs ``.value``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue** `aiida-workgraph #786 <https://github.com/aiidateam/aiida-workgraph/issues/786>`__

.. literalinclude:: ../../tests/test_node_and_serialization.py
   :language: python
   :start-after: # mwe: scalar-dot-value
   :end-before: # end mwe: scalar-dot-value
   :caption: `tests/test_node_and_serialization.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_node_and_serialization.py>`__

In a deferred body a scalar input is a proxy over ``orm.Str``, so you reach through ``.value``; in an eager body it is a proxy over a plain ``str``, ``int(label)`` works and ``label.value`` raises ``AttributeError``.

What already works in a deferred body
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Subscript, ``if`` and ``is None`` see the concrete value in a deferred body

   .. literalinclude:: ../../tests/test_graph_body_values.py
      :language: python
      :start-after: # mwe: deferred-body-values
      :end-before: # end mwe: deferred-body-values
      :caption: `tests/test_graph_body_values.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_graph_body_values.py>`__

   Subscripting the deferred ``orm.Dict`` proxy returns plain Python values (``int``, ``str``, ``None``), so ``==``, ``if`` and ``is None`` compare real values.

Nodes a body needs whole
~~~~~~~~~~~~~~~~~~~~~~~~

**Issue** `aiida-pythonjob #78 <https://github.com/aiidateam/aiida-pythonjob/issues/78>`__ · **Issue** `aiida-pythonjob #83 <https://github.com/aiidateam/aiida-pythonjob/issues/83>`__

.. literalinclude:: ../../tests/test_plain_python_in_bodies.py
   :language: python
   :start-after: # mwe: file-node
   :end-before: # end mwe: file-node
   :caption: `tests/test_plain_python_in_bodies.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_plain_python_in_bodies.py>`__

A ``SinglefileData`` reaches a plain ``@task`` only through a profile-wide deserializer; per task, only ``@task.calcfunction`` receives the node.

What we want: a body sees the Python types its signature declares, on every path.

Should start failing once granted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: ``.value`` on an ``int`` field works

   .. literalinclude:: ../../tests/test_int_should_fail.py
      :language: python
      :start-after: # mwe: int-should-fail
      :end-before: # end mwe: int-should-fail
      :caption: `tests/test_int_should_fail.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_int_should_fail.py>`__

.. dropdown:: ``.get_dict()`` on a ``dict`` input works

   .. literalinclude:: ../../tests/test_dict_should_fail.py
      :language: python
      :start-after: # mwe: dict-should-fail
      :end-before: # end mwe: dict-should-fail
      :caption: `tests/test_dict_should_fail.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dict_should_fail.py>`__

In the wild
~~~~~~~~~~~

aiida-koopmans carries these today:

- Recovering an ``Enum`` member from a proxy or its bare value: `workgraphs/__init__.py#L35 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/__init__.py#L35>`__.
- Rebuilding a namelist override by iterating ``.items()`` rather than trusting ``dict(proxy)``: `workgraphs/dfpt.py#L293 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/dfpt.py#L293>`__.
- Unwrapping a proxied flag to a plain ``bool`` before it is stored: `workgraphs/dfpt.py#L725 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/dfpt.py#L725>`__.
- Coercing a proxied numeric field to ``int``/``float`` before arithmetic: `workgraphs/auto_wannierize.py#L203 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/workgraphs/auto_wannierize.py#L203>`__.
- Rebuilding a parallelization entry into a plain ``dict`` before it reaches a namespace socket: `parallelization.py#L254 <https://github.com/elinscott/aiida-koopmans/blob/main/src/aiida_koopmans/parallelization.py#L254>`__.
