import subprocess
from pathlib import Path

from tests.helpers import run_install, REPO

UNINSTALL = REPO / "uninstall.sh"


def test_uninstall_restores_latest_backup():
    r = run_install(preexisting_claude_md="# original user content\n")
    installed = (r.home / ".claude" / "CLAUDE.md").read_text()
    assert installed != "# original user content\n"

    proc = subprocess.run(
        ["bash", str(UNINSTALL)],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    restored = (r.home / ".claude" / "CLAUDE.md").read_text()
    assert restored == "# original user content\n", \
        "uninstall should restore the pre-install content"


def test_uninstall_is_safe_when_no_backups():
    r = run_install()  # fresh install, no preexisting files, no backups
    proc = subprocess.run(
        ["bash", str(UNINSTALL)],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    # Should not crash; should report "nothing to restore"
    assert proc.returncode == 0, proc.stderr
    assert "nothing to restore" in (proc.stdout + proc.stderr).lower()
