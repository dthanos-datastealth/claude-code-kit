import subprocess
import sys
from pathlib import Path

from tests.helpers import run_install, REPO


def test_running_install_twice_is_safe():
    r = run_install()
    assert r.returncode == 0, r.stderr
    first_log_len = len(r.claude_log.read_text().splitlines())

    # Second invocation in same HOME
    proc = subprocess.run(
        ["bash", str(REPO / "install.sh")],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr

    second_log_len = len(r.claude_log.read_text().splitlines())
    # All steps re-executed (idempotent: marketplace add / plugin install
    # are themselves idempotent in the real `claude` CLI)
    assert second_log_len >= first_log_len

    # A second run must leave the machine in the same state, not accumulate
    # work. On the rules path the kit writes no CLAUDE.md, so there is nothing
    # for the second run to back up — what matters is that the rule files are
    # still correct and the user's override file was not touched.
    rules = r.home / ".claude" / "rules"
    assert (rules / "10-kit-core.md").read_text() == (
        REPO / "claude" / "rules" / "10-kit-core.md").read_text(), \
        "a second install left a kit rule file wrong"
    assert (rules / "00-user-overrides.md").is_file(), \
        "a second install removed the user's override file"
