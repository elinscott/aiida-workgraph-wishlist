"""Link-label validation surprises.

A ``@task`` / ``@task.graph`` function name (and any ``name=`` /
``call_link_label``) becomes an AiiDA link label, which must match
``[A-Za-z0-9_]+`` and may not start with ``_``. Historically the pain was *when*
you found out: not at build time, but silently at runtime -- the offending task
simply never ran and the workgraph reported success.

GRANTED: aiida-workgraph #787 (closes #784) now validates task names as link
labels at build time, raising a clear ``ValueError`` with a fix hint. Promoted
from a wish (``xfail``) to a guard.
"""

from __future__ import annotations

import pytest
from aiida_workgraph import task


def test_underscore_task_name_raises_at_build():
    """GUARD: a ``_underscore`` task name now fails loudly at build time."""

    @task
    def _hidden() -> dict:
        return {"_tag": "underscore", "ran": True}

    @task.graph
    def top():
        _hidden()

    with pytest.raises(ValueError, match="cannot start with an underscore"):
        top.build()
