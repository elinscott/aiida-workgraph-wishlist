Feature requests
================

A TypedDict return annotation builds the same sockets as ``namespace(...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: typeddict-return
   :end-before: # end mwe: typeddict-return
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dynamic_namespace_typing.py>`__

A TypedDict return annotation yields an opaque ``workgraph.dict``, so a downstream namespace consumer cannot link to ``out``. The same shape spelled ``-> Annotated[dict, namespace(out=dynamic(namespace(a=int)))]`` links fine, so this is a parity gap, not a limit.

See ``tests/test_dynamic_namespace_typing.py::test_typeddict_return_annotation_is_consumable`` (wish). Control: ``test_explicit_namespace_gather_is_consumable`` (guard).

What we want: a TypedDict should build the same sockets as the explicit ``namespace(...)`` spelling.

Upstream: `node-graph #154 <https://github.com/scinode/node-graph/issues/154>`__ (issue) and `node-graph #159 <https://github.com/scinode/node-graph/issues/159>`__ (PR, open). The survey expects this may already pass on current node-graph main; the reason string records it failing at 502c1b5.

Subscript a future the way you can multiply one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_zone_ergonomics.py
   :language: python
   :start-after: # mwe: map-destructure
   :end-before: # end mwe: map-destructure
   :caption: `tests/test_zone_ergonomics.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_zone_ergonomics.py>`__

Destructuring a ``Map`` entry needs an unpack task with one output per field, while ``n * 2`` and ``n // 2`` on the same kind of future build ``op_mul`` and ``op_floordiv`` tasks. The refusal is at least loud, which is the model for every other proxy edge.

See ``tests/test_zone_ergonomics.py::test_destructure_map_item_without_unpack_task`` (wish). Controls: ``test_socket_arithmetic_builds_operator_tasks`` and ``test_eager_subscript_of_future_raises_loudly`` (guards).

What we want: ``socket["k"]`` builds an operator task, as ``socket * 2`` already does.

Upstream: `node-graph #156 <https://github.com/scinode/node-graph/issues/156>`__ (issue) and `node-graph #160 <https://github.com/scinode/node-graph/issues/160>`__ (PR, open; carried on our fork as ``op_getitem``). Residue once granted: `node-graph #161 <https://github.com/scinode/node-graph/issues/161>`__, operator tasks discard type information.

Re-scatter a gathered namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../tests/test_dynamic_namespace_typing.py
   :language: python
   :start-after: # mwe: rescatter
   :end-before: # end mwe: rescatter
   :caption: `tests/test_dynamic_namespace_typing.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dynamic_namespace_typing.py>`__

Iterating a fan-out's gathered output inline raises ``has no sub-socket 'items'``, but handing it to another ``@task.graph`` re-scatters it.

See ``tests/test_dynamic_namespace_typing.py::test_gather_then_rescatter`` (guard).

What remains: the inline error should point to the nested-graph spelling.

Upstream: `node-graph #155 <https://github.com/scinode/node-graph/issues/155>`__.
