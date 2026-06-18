"""Shared fixtures: a throwaway AiiDA profile + a run-and-collect helper.

``WorkGraph.run()`` executes the engine in-process against the profile, so no
daemon is needed. Leaf ``@task`` functions in the MWEs return a dict carrying a
unique ``_tag`` so the helper can fish their results back out of the DB after
the run.
"""

from __future__ import annotations

import pytest

pytest_plugins = ["aiida.tools.pytest_fixtures"]


@pytest.fixture
def collect(aiida_profile):
    """Build + run a zero-arg ``@task.graph`` and return the tagged leaf dicts.

    Returns every stored ``orm.Dict`` whose ``_tag`` field is set, as a list of
    plain dicts. MWEs give each leaf a distinct ``_tag`` value.
    """

    def _collect(graph_handle, tag):
        from aiida.orm import Dict, QueryBuilder

        graph_handle.build().run()
        results = []
        for (node,) in QueryBuilder().append(Dict).all():
            data = node.get_dict()
            if data.get("_tag") == tag:
                results.append(data)
        return results

    return _collect
