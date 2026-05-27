"""Pytest config: cleanup test tmp dir at session end."""
import shutil
from pathlib import Path

import pytest

TMP = Path(__file__).resolve().parent / ".tmp"


@pytest.fixture(autouse=True)
def _ensure_tmp_exists():
    TMP.mkdir(exist_ok=True)
    yield


def pytest_sessionfinish(session, exitstatus):
    # Comment out the next line while debugging to inspect test artifacts.
    if TMP.exists():
        shutil.rmtree(TMP, ignore_errors=True)
