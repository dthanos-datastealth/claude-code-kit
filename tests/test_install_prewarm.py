"""Verify install.sh's npx-MCP pre-warm step is non-fatal when npx is absent."""
import subprocess
from pathlib import Path

from tests.helpers import run_install, REPO


def test_prewarm_executes_after_install_plugins():
    """Assert directly on install.sh stdout that the prewarm step ran AFTER
    install_plugins completed. The prewarm step's first log line ('Pre-warming
    npm cache...' or the skip warning) must appear in stdout AFTER the last
    'plugin install' line."""
    r = run_install()
    combined = r.stdout + r.stderr
    # Find the index of the last plugin-install log line
    last_plugin_install = combined.rfind("Installing plugins (reads enabledPlugins")
    # Find the index of the prewarm step's first output
    prewarm_marker = combined.find("Pre-warming npm cache")
    if prewarm_marker < 0:
        prewarm_marker = combined.find("npx not on PATH")
    assert last_plugin_install >= 0, (
        f"install_plugins didn't appear to run; install.sh aborted early:\n{combined}"
    )
    assert prewarm_marker > last_plugin_install, (
        f"prewarm step should run AFTER install_plugins; "
        f"got install_plugins at {last_plugin_install}, prewarm at {prewarm_marker}\n"
        f"combined output:\n{combined}"
    )


def test_install_succeeds_with_no_npx():
    """Pre-warm step must be a soft-fail: if npx isn't on PATH, install.sh
    still completes successfully and prints a warning."""
    # The harness's PATH only includes the fake bin + /usr/bin + /bin.
    # /usr/bin doesn't have npx on macOS or most Linux. So this test
    # exercises the no-npx code path.
    r = run_install()
    assert r.returncode == 0, (
        f"install.sh should succeed even without npx on PATH; got rc={r.returncode}\n"
        f"stdout: {r.stdout}\nstderr: {r.stderr}"
    )
    combined = r.stdout + r.stderr
    # The warning message is what we want when npx is absent
    assert "npx not on PATH" in combined or "Pre-warm complete" in combined, (
        f"prewarm should either pre-warm or skip with warning; saw neither in:\n{combined}"
    )
