Use Enums normally (design)
===========================

Delivery
~~~~~~~~

A bare member cannot cross a socket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-member-socket
   :end-before: # end mwe: enum-member-socket
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

A bare member builds and then dies at run; inside a ``dict`` it is refused at run, loudly. aiida-koopmans pays with an ``aiida.data`` entry point per Enum class, keyed on the class's dotted path.

A graph body gets a proxy, so ``is`` is False
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-graph-body
   :end-before: # end mwe: enum-graph-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

Wrapped as ``orm.EnumData``, the member reaches a graph body as a proxy on both the eager and the deferred path, so ``==`` is True, which the test asserts as its control, and ``is`` is False, and ``third_party``, which tests ``spin is SpinType.COLLINEAR``, takes the wrong branch.

A task body gets a bare ``str``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-task-body
   :end-before: # end mwe: enum-task-body
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

The same ``EnumData`` reaches a plain ``@task`` body as the bare ``str`` ``'collinear'``, so even ``==`` is False one level below where it was True.

The workaround we ship
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-coerce
   :end-before: # end mwe: enum-coerce
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

``coerce`` recovers the member on both paths, at every call site, and accepts a member of a different Enum with the same value.

Membership
~~~~~~~~~~

A member of another Enum is accepted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-foreign-member
   :end-before: # end mwe: enum-foreign-member
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

A ``spin: SpinType`` socket is a generic ``workgraph.annotated`` socket: ``Foreign.COLLINEAR`` builds and runs, and the leaf receives the ``str`` ``'collinear'``. Even ``orm.Int(3)`` builds.

``Literal`` narrowing constrains nothing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../tests/test_enum_coercion.py
   :language: python
   :start-after: # mwe: enum-literal
   :end-before: # end mwe: enum-literal
   :caption: `tests/test_enum_coercion.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_coercion.py>`__

``Literal[SpinType.COLLINEAR, SpinType.NONE]`` constrains nothing: node-graph drops the ``Literal`` to an untyped annotated socket.

Should start failing once granted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: ``.get_member()`` on an Enum input works (guard; must start failing once granted)

   .. literalinclude:: ../../tests/test_enum_should_fail.py
      :language: python
      :start-after: # mwe: enum-should-fail
      :end-before: # end mwe: enum-should-fail
      :caption: `tests/test_enum_should_fail.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_should_fail.py>`__

What we want: the member goes in and the member comes out, on every path.

What it cost us: aiida-quantumespresso branches on ``electronic_type is ElectronicType.INSULATOR``; forwarded from a graph body that was False, and every scf and nscf ran with cold smearing for six months, with no error.

No proxy can satisfy ``is``, so the ask is the plain member, resolved at the boundary.

Two ways to get there
~~~~~~~~~~~~~~~~~~~~~

1. **Builder-side.** ``Literal[SpinType.COLLINEAR, SpinType.NONE]`` on the socket; the builder checks membership once and refuses the build on a mismatch; the body gets the member unchanged.
2. **Pydantic** ``input_model`` (`node-graph #182 <https://github.com/scinode/node-graph/issues/182>`__, `aiida-workgraph #814 <https://github.com/aiidateam/aiida-workgraph/issues/814>`__): richer rules, but a pivot. Is 1 a subset of 2?

Upstream: `node-graph #152 <https://github.com/scinode/node-graph/issues/152>`__, `node-graph #175 <https://github.com/scinode/node-graph/issues/175>`__, `node-graph #176 <https://github.com/scinode/node-graph/issues/176>`__, `node-graph #178 <https://github.com/scinode/node-graph/issues/178>`__ with `aiida-workgraph #800 <https://github.com/aiidateam/aiida-workgraph/issues/800>`__.
