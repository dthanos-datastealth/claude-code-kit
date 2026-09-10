"""`upgrade.sh --status` must report drift, because it says it does.

The script's own header advertises "--status  Report current install state +
drift + unresolved conflicts", and skills/status/SKILL.md promises "Whether
live CLAUDE.md and settings.json SHA matches the recorded SHA (drift
detection — user has manually edited a kit-owned file)".

Neither was implemented. On a machine whose settings.json had genuinely
drifted, --status printed the version block, "Unresolved conflicts: (none)"
and the backup list, and said nothing about drift. A status command that
reports health it never measured is worse than one that reports nothing: it
ends the investigation.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tests.helpers import REPO

UPGRADE_SH = REPO / "scripts" / "upgrade.sh"


def _run_status(home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(UPGRADE_SH), "--status"],
        env={
            "HOME": str(home),
            "CLAUDE_HOME": str(home / ".claude"),
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "LANG": "C.UTF-8",
        },
        text=True,
        capture_output=True,
    )


def _install_with_marker(home: Path, settings_text: str) -> None:
    cd = home / ".claude"
    cd.mkdir(parents=True, exist_ok=True)
    (cd / "settings.json").write_text(settings_text)
    sha = hashlib.sha256(settings_text.encode()).hexdigest()
    (cd / ".kit-version").write_text(json.dumps({
        "installed_at": "2026-09-10T00:00:00Z",
        "channel": "prerelease",
        "commit": "abc1234",
        "claude_md_sha256": "",
        "settings_sha256": sha,
    }) + "\n")


def test_status_reports_match_when_settings_are_untouched(tmp_path):
    """Positive control. Without it, a --status that printed DRIFTED
    unconditionally would satisfy the test below."""
    _install_with_marker(tmp_path, '{"effortLevel": "xhigh"}\n')
    r = _run_status(tmp_path)
    assert r.returncode == 0, r.stderr
    out = r.stdout + r.stderr
    assert "settings.json" in out
    assert "DRIFTED" not in out, f"reported drift on an untouched file:\n{out}"


def test_status_reports_drift_when_settings_were_edited(tmp_path):
    _install_with_marker(tmp_path, '{"effortLevel": "xhigh"}\n')
    (tmp_path / ".claude" / "settings.json").write_text('{"effortLevel": "low"}\n')
    r = _run_status(tmp_path)
    assert r.returncode == 0, r.stderr
    out = r.stdout + r.stderr
    assert "DRIFTED" in out, (
        "settings.json no longer matches the recorded SHA and --status must "
        f"say so. Got:\n{out}"
    )


def test_status_drift_check_is_quiet_without_a_marker(tmp_path):
    """No .kit-version means nothing to compare against; say that rather
    than claiming either state."""
    cd = tmp_path / ".claude"
    cd.mkdir(parents=True)
    (cd / "settings.json").write_text("{}\n")
    r = _run_status(tmp_path)
    assert r.returncode == 0
    assert "DRIFTED" not in (r.stdout + r.stderr)


def _fake_claude_bin(home: Path) -> Path:
    """A `claude` reporting a version above the rules floor.

    Without one, kit_rules_supported() is false and upgrade.sh takes the
    pre-2.0.64 CLAUDE.md merge path instead of the one under test.
    """
    bin_dir = home / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake = bin_dir / "claude"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "--version" ]; then echo "2.1.251 (Claude Code)"; exit 0; fi\n'
        "exit 0\n"
    )
    fake.chmod(0o755)
    return bin_dir


def _run_dry_run(home: Path) -> subprocess.CompletedProcess:
    bin_dir = _fake_claude_bin(home)
    return subprocess.run(
        ["bash", str(UPGRADE_SH), "--dry-run"],
        env={
            "HOME": str(home),
            "CLAUDE_HOME": str(home / ".claude"),
            "PATH": f"{bin_dir}:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "LANG": "C.UTF-8",
        },
        text=True,
        capture_output=True,
    )


def test_dry_run_prints_the_settings_delta(tmp_path):
    """README calls --dry-run "preview the diff", and skills/upgrade/SKILL.md
    builds a four-way confirmation prompt on top of it. Before this, the
    entire output was four status lines: the user was asked to approve a
    change they could not see."""
    _install_with_marker(tmp_path, json.dumps({
        "enabledPlugins": {"mine@somewhere": True},
        "env": {"MY_OWN": "1"},
    }) + "\n")
    r = _run_dry_run(tmp_path)
    assert r.returncode == 0, r.stderr
    out = r.stdout + r.stderr
    assert "plugins_added_in_live" in out, f"no delta in dry-run output:\n{out}"
    assert "mine@somewhere" in out, (
        "the delta must name the user's own plugin, which is the thing a "
        f"reader is being asked to approve keeping:\n{out}"
    )


def test_dry_run_writes_nothing(tmp_path):
    """Positive control for the test above: printing a delta must not have
    turned the dry run into a real one."""
    settings = json.dumps({"enabledPlugins": {"mine@somewhere": True}}) + "\n"
    _install_with_marker(tmp_path, settings)
    before = (tmp_path / ".claude" / "settings.json").read_text()
    r = _run_dry_run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / ".claude" / "settings.json").read_text() == before
