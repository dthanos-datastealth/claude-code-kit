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


def test_install_stops_when_npx_is_missing():
    """npx is a hard prerequisite, so its absence stops the install.

    This test previously asserted the opposite — that install.sh completes
    with a warning when npx is absent — on the stated basis that the harness
    never put npx on PATH. Both halves stopped being true: preflight now
    requires npx, and the harness stubs it. Its assertion
    (`"npx not on PATH" in out or "Pre-warm complete" in out`) was satisfied
    by the pre-warm branch, so it passed while testing nothing, and deleting
    the guard it named left all three tests in this file green.

    npx is required because playwright, chrome-devtools and context7 launch
    through it. Failing at preflight, by name, beats installing cleanly and
    leaving three MCP servers dead.
    """
    r = run_install(omit_tools=["npx"])
    assert r.returncode != 0, (
        f"install.sh must not complete without npx; got rc={r.returncode}\n"
        f"stdout: {r.stdout}\nstderr: {r.stderr}"
    )
    assert "npx" in (r.stdout + r.stderr)


def test_prewarm_runs_when_npx_is_present():
    """Positive control: with npx present the pre-warm step actually runs,
    so the test above is failing for the absence and not for some other
    reason."""
    r = run_install()
    assert r.returncode == 0, r.stderr
    assert "Pre-warm complete" in (r.stdout + r.stderr)


def test_version_marker_records_the_release_channel():
    """`:status` reads this file verbatim, so the channel an install came from
    has to be in it — otherwise a tester on the prerelease channel and a user
    on stable produce indistinguishable status output."""
    import json

    r = run_install()
    marker = json.loads((r.home / ".claude" / ".kit-version").read_text())
    assert marker["channel"], "channel must be recorded"
    assert marker["commit"], "commit must be recorded"
    # rolled_back_to is the rollback slot and must not be reused for this.
    assert "rolled_back_to" not in marker
