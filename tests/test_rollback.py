"""Tests for scripts/upgrade.sh --rollback and the relationship between
:rollback (soft) and uninstall.sh (nuclear)."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPGRADE_SH = REPO / "scripts" / "upgrade.sh"
UNINSTALL_SH = REPO / "uninstall.sh"


def _run(args: list[str], home: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "CLAUDE_HOME": str(home / ".claude"),
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "LANG": "C.UTF-8",
        **(env_extra or {}),
    }
    return subprocess.run(["bash"] + args, env=env, text=True, capture_output=True)


def _setup_install_with_backup(tmp_path: Path) -> tuple[Path, str]:
    """Create a fake ~/.claude/ with a timestamped backup; return (home, backup_id)."""
    home = tmp_path
    cd = home / ".claude"
    cd.mkdir()
    (cd / "CLAUDE.md").write_text("# CURRENT VERSION\n")
    (cd / "settings.json").write_text('{"effortLevel": "max"}\n')
    (cd / ".kit-version").write_text('{"installed_at": "2026-05-29T00:00:00Z"}\n')
    # Create a backup representing a prior state
    bk_id = "2026-05-28T12-00-00Z"
    bk = cd / "backups" / bk_id
    bk.mkdir(parents=True)
    (bk / "CLAUDE.md").write_text("# OLDER VERSION (from backup)\n")
    (bk / "settings.json").write_text('{"effortLevel": "low"}\n')
    return home, bk_id


def test_case_13_rollback_restores_files_from_backup(tmp_path):
    home, bk_id = _setup_install_with_backup(tmp_path)
    r = _run([str(UPGRADE_SH), "--rollback", bk_id], home)
    assert r.returncode == 0, f"rollback failed: {r.stderr}"
    assert (home / ".claude" / "CLAUDE.md").read_text() == "# OLDER VERSION (from backup)\n"
    assert json.loads((home / ".claude" / "settings.json").read_text())["effortLevel"] == "low"


def test_case_14_rollback_appends_history_entry(tmp_path):
    home, bk_id = _setup_install_with_backup(tmp_path)
    r = _run([str(UPGRADE_SH), "--rollback", bk_id], home)
    assert r.returncode == 0
    hist = (home / ".claude" / ".kit-version.history.jsonl").read_text()
    assert "rollback" in hist
    assert bk_id in hist


def test_case_14b_rollback_updates_kit_version_to_restored_state(tmp_path):
    """Per docs/upgrading.md + rollback skill: rollback updates .kit-version
    to reflect the just-restored content (not the kit-template SHAs)."""
    home, bk_id = _setup_install_with_backup(tmp_path)
    r = _run([str(UPGRADE_SH), "--rollback", bk_id], home)
    assert r.returncode == 0
    kv = json.loads((home / ".claude" / ".kit-version").read_text())
    # rolled_back_to field references the backup id
    assert kv.get("rolled_back_to") == bk_id
    # SHAs match the actually-on-disk restored files (the OLDER versions)
    import hashlib
    md_sha = hashlib.sha256((home / ".claude" / "CLAUDE.md").read_bytes()).hexdigest()
    settings_sha = hashlib.sha256((home / ".claude" / "settings.json").read_bytes()).hexdigest()
    assert kv.get("claude_md_sha256") == md_sha
    assert kv.get("settings_sha256") == settings_sha


def test_case_15_rollback_nonexistent_backup_errors_cleanly(tmp_path):
    home, _ = _setup_install_with_backup(tmp_path)
    pre_md = (home / ".claude" / "CLAUDE.md").read_text()
    r = _run([str(UPGRADE_SH), "--rollback", "no-such-backup"], home)
    assert r.returncode != 0
    # CLAUDE.md should be unchanged
    assert (home / ".claude" / "CLAUDE.md").read_text() == pre_md


def test_case_16_status_lists_available_backups(tmp_path):
    home, bk_id = _setup_install_with_backup(tmp_path)
    r = _run([str(UPGRADE_SH), "--status"], home)
    assert r.returncode == 0
    assert bk_id in r.stdout


def test_case_17_uninstall_after_rollback_works_cleanly(tmp_path):
    """uninstall.sh after a rollback restores the most-recent backup AND
    cleans up the kit state files (.kit-version, .kit-cache, .kit-conflicts)."""
    home, bk_id = _setup_install_with_backup(tmp_path)
    # First rollback (changes .kit-version.history.jsonl)
    r1 = _run([str(UPGRADE_SH), "--rollback", bk_id], home)
    assert r1.returncode == 0
    assert (home / ".claude" / ".kit-version").exists()
    # Now uninstall — should restore latest backup AND remove kit state files
    r2 = _run([str(UNINSTALL_SH)], home)
    assert r2.returncode == 0, f"uninstall failed: {r2.stderr}"
    # State files must be removed
    assert not (home / ".claude" / ".kit-version").exists(), \
        ".kit-version should be removed by uninstall"
    assert not (home / ".claude" / ".kit-version.history.jsonl").exists(), \
        ".kit-version.history.jsonl should be removed by uninstall"
    # CLAUDE.md restored from the most recent backup (the same one we rolled back to)
    assert (home / ".claude" / "CLAUDE.md").read_text() == "# OLDER VERSION (from backup)\n"


def test_status_with_no_install_marker(tmp_path):
    """--status against a clean HOME (no .kit-version) reports pre-tool state."""
    home = tmp_path
    (home / ".claude").mkdir()
    r = _run([str(UPGRADE_SH), "--status"], home)
    assert r.returncode == 0
    assert "No kit version marker" in r.stdout or "fresh install" in r.stdout.lower()
