"""Shared fixtures: a throwaway AiiDA profile.

``WorkGraph.run()`` executes the engine in-process against the profile, so no
daemon is needed.
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

pytest_plugins = ["aiida.tools.pytest_fixtures"]
