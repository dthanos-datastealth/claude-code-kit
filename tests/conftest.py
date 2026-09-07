"""Pytest config: per-session scratch dir, removed at session end.

The scratch root is shared between concurrent pytest sessions, so each session
gets its own subdirectory and removes only that. Removing the shared root would
delete a concurrently-running session's isolated HOMEs out from under it.
"""
import os
import shutil

import pytest

from tests.helpers import SESSION_TMP, TMP_ROOT


def _pid_alive(pid: int) -> bool:
    # os.kill(0, ...) addresses the whole process group and os.kill(-n, ...) a
    # group by id; neither is a directory we could have created, so treat any
    # non-positive value as not-ours and keep it.
    if pid <= 0:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True          # exists, owned by someone else
    return True


def pytest_sessionstart(session):
    """Reap scratch dirs left by sessions that were killed.

    `pytest_sessionfinish` does not run on SIGKILL, a crash or a CI timeout, so
    those directories persist with their isolated HOME trees inside — leaking
    disk, and making the `TMP_ROOT.rmdir()` below fail for every later session.
    """
    if not TMP_ROOT.is_dir():
        return
    for child in TMP_ROOT.glob("session-*"):
        try:
            pid = int(child.name.split("-", 1)[1])
        except (IndexError, ValueError):
            continue
        if not _pid_alive(pid):
            shutil.rmtree(child, ignore_errors=True)


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
