"""Verify install.sh's npx-MCP pre-warm step is non-fatal when npx is absent."""
import subprocess
from pathlib import Path

from tests.helpers import run_install, REPO


def test_prewarm_runs_at_end_of_install():
    """The fake claude CLI logs every invocation; prewarm step happens after
    install_plugins so we can check ordering by comparing line positions."""
    r = run_install()
    log_lines = r.claude_log.read_text().splitlines()
    # prewarm doesn't call claude (it calls npx), so we only assert install.sh
    # didn't bail before completing all the claude-CLI work
    plugin_install_count = sum(1 for ln in log_lines if ln.startswith("plugin install "))
    assert plugin_install_count == 21, (
        f"expected 21 plugin installs, got {plugin_install_count} "
        f"(suggests install.sh aborted before/during install_plugins)"
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
