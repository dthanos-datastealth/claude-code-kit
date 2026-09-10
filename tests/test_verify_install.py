"""scripts/verify-install.py — the artifact assertions the isolation harness runs.

Extracted from test-install-isolated.sh so it can be tested directly. The
harness asserted `CLAUDE.md` unconditionally, which install.sh deliberately
stopped writing at Claude Code 2.0.64, so the harness failed on every run
against any current CLI — and failed at that assertion, four steps before the
leak check that is the only reason the harness exists. Nothing was proving
isolation, and nothing said so.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tests.helpers import REPO

VERIFY = REPO / "scripts" / "verify-install.py"
KIT_RULES = REPO / "claude" / "rules"


def _run(home: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(VERIFY), str(home / ".claude"), *args],
        text=True, capture_output=True,
    )


def _populate(home: Path, *, rules: bool = True, claude_md: bool = False) -> Path:
    cd = home / ".claude"
    (cd / "memory").mkdir(parents=True, exist_ok=True)
    (cd / "memory" / "MEMORY.md").write_text("# Memory Index\n")
    (cd / "docs" / "tools").mkdir(parents=True, exist_ok=True)
    (cd / "docs" / "tools" / "berry.md").write_text("# berry\n")
    (cd / "settings.json").write_text(json.dumps({
        "enabledPlugins": {"a@b": True}, "env": {}
    }))
    if rules:
        (cd / "rules").mkdir(exist_ok=True)
        for src in KIT_RULES.glob("*.md"):
            (cd / "rules" / src.name).write_text(src.read_text())
    if claude_md:
        (cd / "CLAUDE.md").write_text("# kit\n")
    return cd


def test_passes_on_a_rules_based_install(tmp_path):
    """The shape install.sh actually produces on a current CLI: rules/, no
    CLAUDE.md. This is what the old harness rejected."""
    _populate(tmp_path, rules=True, claude_md=False)
    r = _run(tmp_path, "--expect-rules")
    assert r.returncode == 0, r.stdout + r.stderr


def test_fails_when_rules_are_missing_on_a_rules_based_install(tmp_path):
    _populate(tmp_path, rules=False, claude_md=False)
    r = _run(tmp_path, "--expect-rules")
    assert r.returncode != 0
    assert "rules" in (r.stdout + r.stderr).lower()


def test_does_not_require_claude_md_above_the_version_floor(tmp_path):
    """install.sh leaves CLAUDE.md to the user from 2.0.64 on. Requiring it
    is what broke the harness."""
    _populate(tmp_path, rules=True, claude_md=False)
    r = _run(tmp_path, "--expect-rules")
    assert r.returncode == 0, (
        "CLAUDE.md is the user's file above the floor and must not be "
        f"required:\n{r.stdout}{r.stderr}"
    )


def test_requires_claude_md_below_the_version_floor(tmp_path):
    """Below 2.0.64 ~/.claude/rules is ignored, so the CLAUDE.md template is
    the only way the kit's instructions reach Claude at all."""
    _populate(tmp_path, rules=False, claude_md=False)
    r = _run(tmp_path, "--expect-claude-md")
    assert r.returncode != 0
    assert "CLAUDE.md" in (r.stdout + r.stderr)


def test_reports_every_missing_artifact_not_just_the_first(tmp_path):
    """A harness that stops at the first failure hides the rest, which is how
    one stale assertion masked the leak check."""
    cd = tmp_path / ".claude"
    cd.mkdir(parents=True)
    (cd / "settings.json").write_text("{}")
    r = _run(tmp_path, "--expect-rules")
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "memory/MEMORY.md" in out and "docs/tools" in out, (
        f"expected all missing artifacts listed, got:\n{out}"
    )
