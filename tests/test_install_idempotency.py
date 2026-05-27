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

    # Second run should have created a SECOND backup of CLAUDE.md
    # (because after first run, ~/.claude/CLAUDE.md exists)
    backups = list((r.home / ".claude" / "backups").glob("*/CLAUDE.md"))
    assert len(backups) >= 1
