aiida-workgraph wishlist
========================

What I want:

- starting with plain, well-annotated Python (``TypedDict``, ``dataclass``, ``Enum``)
- wrap with ``@task`` or ``@task.graph`` (ideally without any wrapper args)
- and have it work out-of-the-box.

Writing aiida-koopmans against aiida-workgraph, that has not been the case, as the examples below show.

Overarching questions
---------------------

- What is guaranteed inside a body? *Ideally: the Python type the signature declares, the same for* ``@task`` *and* ``@task.graph``, *on every path — eager, deferred, restored from a checkpoint.*
- Who owns serialization? *Proposed: the engine, at the socket boundary. A body never names an* ``orm`` *type; where a node has no plain-Python counterpart, we want one (see below).*

  A class like ``StructureData`` does two jobs
  - it is the stored, serializable record
  - it is the object you handle in a function body.
  We would split those: one class responsible for serialization, and one convenient Python object for interacting with a structure, and only the latter appears in function bodies. See also: ``BandsData``, ``RemoteData``, ``FolderData``, ...
- How to get Enums working? Singletons go against ``TaggedValue`` design and ``is`` becomes impossible. Serialization also currently gives lots of surprises. *Proposed: member in, member out; a* ``Literal[...]`` *subset of members is enforced by the builder alone, and nothing downstream coerces.*
- Contracts: to encode all of this, do we need to turn to a pydantic ``input_model``? (`node-graph #182 <https://github.com/scinode/node-graph/issues/182>`_, `aiida-workgraph #814 <https://github.com/aiidateam/aiida-workgraph/issues/814>`_) *I would hesitate to recommend a full pydantic pivot if the enum-subset contract can be guaranteed.*
- Logistics: which code should I be writing against, and where do bugs and PRs go, especially now that aiida-workgraph and node-graph are no longer compatible with aiida-core?

1. Enums
--------

A bare member crosses a socket only with a serializer registered per ``Enum`` class; a graph body then sees a proxy and a task body a ``str``. Full set: :doc:`examples/enums`.

.. literalinclude:: ../tests/wishlist_types.py
   :language: python
   :pyobject: SpinType
   :caption: `tests/wishlist_types.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/wishlist_types.py>`__

1.1 What we would like to write
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_enum_want.py
   :language: python
   :start-after: # mwe: enum-want
   :end-before: # end mwe: enum-want
   :caption: `tests/test_enum_want.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_want.py>`__

1.2 What we need to write today
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_enum_today.py
   :language: python
   :start-after: # mwe: enum-today
   :end-before: # end mwe: enum-today
   :caption: `tests/test_enum_today.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_enum_today.py>`__

Once granted, ``spin.get_member()`` in a body must raise; the suite pins that.

1.3 Type narrowing
~~~~~~~~~~~~~~~~~~

ph.x handles two of the three spin regimes. We want to say so on the task's socket and have the builder check it where the member is known; a member that only arrives at run is checked at run by the same rule.

.. literalinclude:: ../tests/test_narrow_want.py
   :language: python
   :start-after: # mwe: narrow-want
   :end-before: # end mwe: narrow-want
   :caption: `tests/test_narrow_want.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_narrow_want.py>`__

.. literalinclude:: ../tests/test_narrow_today.py
   :language: python
   :start-after: # mwe: narrow-today
   :end-before: # end mwe: narrow-today
   :caption: `tests/test_narrow_today.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_narrow_today.py>`__

2. Plain Python in bodies
-------------------------

An ``int`` declared in the signature arrives as ``orm.Int`` inside a deferred graph body. Full set: :doc:`examples/no-orm`.

.. literalinclude:: ../tests/wishlist_types.py
   :language: python
   :pyobject: Settings
   :caption: `tests/wishlist_types.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/wishlist_types.py>`__

2.1 What we would like to write
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_int_want.py
   :language: python
   :start-after: # mwe: int-want
   :end-before: # end mwe: int-want
   :caption: `tests/test_int_want.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_int_want.py>`__

2.2 What we need to write today
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_int_today.py
   :language: python
   :start-after: # mwe: int-today
   :end-before: # end mwe: int-today
   :caption: `tests/test_int_today.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_int_today.py>`__

Once granted, ``cfg.nspin.value`` in a body must raise; the suite pins that.

3. Eager and deferred bodies
----------------------------

The same body sees a ``dict`` at top level and an ``orm.Dict`` when nested; which one is the caller's choice. Full set: :doc:`examples/no-orm`, :doc:`examples/annotated-python`.

3.1 What we would like to write
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_dict_want.py
   :language: python
   :start-after: # mwe: dict-want
   :end-before: # end mwe: dict-want
   :caption: `tests/test_dict_want.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dict_want.py>`__

3.2 What we need to write today
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../tests/test_dict_today.py
   :language: python
   :start-after: # mwe: dict-today
   :end-before: # end mwe: dict-today
   :caption: `tests/test_dict_today.py <https://github.com/elinscott/aiida-workgraph-wishlist/blob/refresh-2026-09/tests/test_dict_today.py>`__

Once granted, ``overrides.get_dict()`` in a body must raise; the suite pins that.

Everything else
---------------

- :doc:`examples/annotated-python` — ``None`` and ``TypedDict`` fields go missing
- :doc:`examples/echo-input` — a graph cannot return its own input
- :doc:`examples/two-serializations` — the serialization you can test is not the one that runs
- :doc:`examples/zones` — ``While`` state must go through ``ctx``
- :doc:`examples/feature-requests`, :doc:`examples/bugs`

Every example is a test in ``tests/``; :doc:`how-to-run` runs them and builds this page.

.. toctree::
   :hidden:
   :maxdepth: 1

   examples/annotated-python
   examples/no-orm
   examples/enums
   examples/echo-input
   examples/two-serializations
   examples/zones
   examples/feature-requests
   examples/bugs
   how-to-run
