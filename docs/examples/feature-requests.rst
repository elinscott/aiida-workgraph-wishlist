Feature requests
================

A ``TypedDict`` return annotation builds the same sockets as ``namespace(...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: typeddict-return
   :end-before: # end mwe: typeddict-return
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dynamic_namespace_typing.py>`__

A ``TypedDict`` return annotation yields an opaque ``workgraph.dict``; the same shape spelled with ``namespace(...)`` links fine.

What we want: a ``TypedDict`` should build the same sockets as the explicit ``namespace(...)`` spelling.

Subscript a future the way you can multiply one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_zone_ergonomics.py
   :language: python
   :start-after: # mwe: map-destructure
   :end-before: # end mwe: map-destructure
   :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

Destructuring a ``Map`` entry needs an unpack task, while ``n * 2`` on the same future builds an operator task.

What we want: ``socket["k"]`` builds an operator task, as ``socket * 2`` already does.

Re-scatter a gathered namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: rescatter
   :end-before: # end mwe: rescatter
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dynamic_namespace_typing.py>`__

Iterating a fan-out's gathered output inline raises ``has no sub-socket 'items'``, but handing it to another ``@task.graph`` re-scatters it.

What remains: the inline error should point to the nested-graph spelling.

Upstream issues and PRs
~~~~~~~~~~~~~~~~~~~~~~~

- A ``TypedDict`` return annotation builds the same sockets as ``namespace(...)``: `node-graph #154 <https://github.com/scinode/node-graph/issues/154>`__ and `node-graph #159 <https://github.com/scinode/node-graph/issues/159>`__.
- Subscript a future the way you can multiply one: `node-graph #156 <https://github.com/scinode/node-graph/issues/156>`__ and `node-graph #160 <https://github.com/scinode/node-graph/issues/160>`__.
- Re-scatter a gathered namespace: `node-graph #155 <https://github.com/scinode/node-graph/issues/155>`__.
