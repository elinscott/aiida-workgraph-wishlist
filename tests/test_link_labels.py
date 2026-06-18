"""Link-label validation surprises.

A ``@task`` / ``@task.graph`` function name (and any ``name=`` /
``call_link_label``) becomes an AiiDA link label, which must match
``[A-Za-z0-9_]+`` and may not start with ``_``. The pain is *when* you find out:
not at build time, but silently at runtime -- the offending task simply never
runs and the workgraph reports success. We wish this were a build-time error.
"""

from __future__ import annotations

import pytest
from aiida_workgraph import task


@pytest.mark.xfail(
    reason="aiida-workgraph 0.8.1: a leading-underscore @task name is an invalid "
    "AiiDA link label, but instead of failing at build the task is silently "
    "skipped and the workgraph reports success. We wish it raised at build time "
    "(forced renames like dft_n_minus_1, and no _private @task names)."
)
def test_underscore_task_name_is_not_silently_skipped(collect):
    """WISH: a ``_underscore`` task name fails loudly, not silently."""

    @task
    def _hidden() -> dict:
        return {"_tag": "underscore", "ran": True}

    @task.graph
    def top():
        _hidden()

    rs = collect(top, "underscore")
    assert rs and rs[0]["ran"] is True
