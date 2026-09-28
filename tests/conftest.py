"""Shared fixtures: a throwaway AiiDA profile + a run-and-collect helper.

``WorkGraph.run()`` executes the engine in-process against the profile, so no
daemon is needed. Leaf ``@task`` functions in the MWEs return a dict carrying a
unique ``_tag`` so the helper can fish their results back out of the DB after
the run.
"""

from __future__ import annotations

import os

# aiida-core reads ~/.aiida/config.json at import and migrates it to its own schema
# without asking; this repo pins its own aiida-core, so keep it on a config of its own.
os.environ.setdefault("AIIDA_PATH", os.path.expanduser("~/.aiida-wishlist"))

from aiida.manage.configuration import get_config  # noqa: E402

# Some imports below load the configuration without creating it; make sure the
# file exists first, or a fresh checkout fails on the first test module.
get_config(create=True)

import pytest  # noqa: E402

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
