How to run
==========

.. code-block:: text

   uv sync
   uv run pytest -q
   uv run pytest -rX

The last command lists the open wishes. The suite uses its own config under ``~/.aiida-wishlist`` and a throwaway profile, so it never touches a real AiiDA profile.

This page builds with:

.. code-block:: text

   uv run --group docs sphinx-build -W -b html docs docs/_build/html

aiida-core is pinned to v2.9.1: aiida-core main has absorbed plumpy, while aiida-workgraph main still imports plumpy without declaring it.
