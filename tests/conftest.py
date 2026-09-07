"""Pytest config: per-session scratch dir, removed at session end.

The scratch root is shared between concurrent pytest sessions, so each session
gets its own subdirectory and removes only that. Removing the shared root would
delete a concurrently-running session's isolated HOMEs out from under it.
"""
import shutil

import pytest

from tests.helpers import SESSION_TMP, TMP_ROOT


@pytest.fixture(autouse=True)
def _ensure_tmp_exists():
    SESSION_TMP.mkdir(parents=True, exist_ok=True)
    yield


def pytest_sessionfinish(session, exitstatus):
    # Comment out the next line while debugging to inspect test artifacts.
    shutil.rmtree(SESSION_TMP, ignore_errors=True)
    # Take the shared root too, but only when no other session is using it.
    try:
        TMP_ROOT.rmdir()
    except OSError:
        pass
