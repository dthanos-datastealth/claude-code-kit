import subprocess
from pathlib import Path

from tests.helpers import run_install, REPO

UNINSTALL = REPO / "uninstall.sh"


def test_uninstall_restores_latest_backup():
    """Only the legacy path replaces CLAUDE.md, so only it has something to
    restore. On the rules path the kit never wrote the file."""
    r = run_install(preexisting_claude_md="# original user content\n",
                    extra_env={"CCK_FAKE_CLAUDE_VERSION": "2.0.63"})
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
    # Should not crash, should say there is nothing to restore, and should
    # still remove what the kit installed — a clean-machine install makes no
    # backup, and that must not mean it can never be uninstalled.
    out = (proc.stdout + proc.stderr).lower()
    assert proc.returncode == 0, proc.stderr
    assert "no backup to restore from" in out, out
    assert not (r.home / ".claude" / "docs").exists(), "docs survived with no backup present"


def test_uninstall_removes_the_kits_rule_files():
    """Leaving the kit has to mean leaving its rules behind too, or every future
    session keeps loading instructions from a kit that is no longer installed."""
    r = run_install()
    rules = r.home / ".claude" / "rules"
    assert (rules / "10-kit-core.md").is_file(), "precondition: rules were installed"
    (rules / "00-user-overrides.md").write_text("# mine\n- always use tabs\n")

    proc = subprocess.run(
        ["bash", str(UNINSTALL)],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    leftover = sorted(p.name for p in rules.glob("*-kit-*.md")) if rules.is_dir() else []
    assert not leftover, f"kit rules survived uninstall: {leftover}"
    if rules.is_dir():
        mine = rules / "00-user-overrides.md"
        assert mine.is_file() and "always use tabs" in mine.read_text(), \
            "uninstall removed the user's own overrides"


def test_uninstall_removes_the_kits_docs():
    r = run_install()
    docs = r.home / ".claude" / "docs"
    assert docs.is_dir(), "precondition: docs were installed"
    subprocess.run(["bash", str(UNINSTALL)],
                   env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin",
                        "LANG": "C.UTF-8"}, text=True, capture_output=True)
    assert not docs.exists(), "kit docs survived uninstall"


def test_uninstall_restores_the_users_own_rule_files_from_backup(tmp_path):
    """A backup carries rules/, so uninstall can put the user's own files
    back rather than leaving whatever the last upgrade wrote.

    The kit's six files are removed either way. What must survive is
    00-user-overrides.md and anything else the user authored — the part they
    cannot recover from the repository.
    """
    home = tmp_path
    cd = home / ".claude"
    (cd / "rules").mkdir(parents=True)
    (cd / "settings.json").write_text("{}\n")
    (cd / ".kit-version").write_text('{"installed_at": "2026-09-10T00:00:00Z"}\n')
    # Live state: kit files present, and the user's override has been
    # clobbered since the backup was taken.
    (cd / "rules" / "10-kit-core.md").write_text("# kit\n")
    (cd / "rules" / "00-user-overrides.md").write_text("# CLOBBERED\n")

    bk = cd / "backups" / "2026-09-09T00-00-00Z"
    (bk / "rules").mkdir(parents=True)
    (bk / "settings.json").write_text("{}\n")
    (bk / "rules" / "10-kit-core.md").write_text("# kit\n")
    (bk / "rules" / "00-user-overrides.md").write_text("# MY RULES\n")
    (bk / "rules" / "99-mine.md").write_text("# also mine\n")

    r = subprocess.run(
        ["bash", str(UNINSTALL)],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert r.returncode == 0, r.stderr

    assert (cd / "rules" / "00-user-overrides.md").read_text() == "# MY RULES\n"
    assert (cd / "rules" / "99-mine.md").read_text() == "# also mine\n"
    assert not (cd / "rules" / "10-kit-core.md").exists(), (
        "kit rule files must not survive an uninstall, restored or otherwise"
    )
