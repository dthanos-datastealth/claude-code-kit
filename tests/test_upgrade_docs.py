"""Upgrading must refresh ~/.claude/docs/, not just CLAUDE.md and settings."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
UPGRADE_SH = REPO / "scripts" / "upgrade.sh"


def _top_level_docs() -> list[str]:
    body = (REPO / "scripts" / "_kit_docs.sh").read_text()
    block = re.search(r"^TOP_LEVEL_DOCS=\((.*?)^\)", body, re.S | re.M)
    assert block, "TOP_LEVEL_DOCS not found in scripts/_kit_docs.sh"
    return re.findall(r'"([^"]+)"', block.group(1))


PREVIOUS_RELEASE = REPO / "tests" / "fixtures" / "previous-release-CLAUDE.md"


def _existing_install(home: Path) -> None:
    """A machine installed from the previous release: docs present but stale.

    The cached baseline matches the live file, which is what a clean install
    leaves behind and what makes this a clean upgrade rather than a conflict.
    """
    cd = home / ".claude"
    (cd / "docs" / "tools").mkdir(parents=True)
    (cd / ".kit-cache").mkdir(parents=True)
    previous = PREVIOUS_RELEASE.read_text()
    (cd / "CLAUDE.md").write_text(previous)
    (cd / ".kit-cache" / "CLAUDE.md").write_text(previous)
    (cd / "settings.json").write_text(json.dumps({"env": {"MINE": "1"}}) + "\n")
    (cd / ".kit-version").write_text(json.dumps({"installed_at": "2026-05-29T00:00:00Z"}) + "\n")
    # One stale doc and one that the newer release adds.
    (cd / "docs" / "prereqs.md").write_text("# prereqs\n\nOLD CONTENT\n")
    (cd / "docs" / "tools" / "berry.md").write_text("# berry\n\nOLD CONTENT\n")


def _run_upgrade(home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(UPGRADE_SH), "--apply"],
        env={"HOME": str(home), "CLAUDE_HOME": str(home / ".claude"),
             "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )


@pytest.fixture(scope="module")
def upgraded():
    """One upgrade for the whole module.

    All three tests here set up the same previous-release install, run the same
    `upgrade.sh --apply`, and only read from the result. Repeating that spawn
    three times is work the first call already did; nothing below mutates the
    tree, so one run serves all three.
    """
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _existing_install(home)
        res = _run_upgrade(home)
        assert res.returncode == 0, res.stderr
        yield home


def test_upgrade_installs_docs_the_release_adds(upgraded):
    """CLAUDE.md points at `~/.claude/docs/*`; an upgrade must put them there.

    `copy_docs` lived only in install.sh, so an upgrade refreshed CLAUDE.md and
    settings and nothing else. A user upgrading onto this release got a
    CLAUDE.md referencing `verification-standards.md` four times and no such
    file on disk — and kept the previous release's copy of every other doc.
    """
    home = upgraded
    dst = home / ".claude" / "docs"
    for name in _top_level_docs():
            assert (dst / name).exists(), f"{name} missing from ~/.claude/docs after upgrade"

    shipped = {p.name for p in (REPO / "docs" / "tools").glob("*.md")}
    installed = {p.name for p in (dst / "tools").glob("*.md")}
    assert shipped == installed, f"tools docs differ: missing {shipped - installed}"


def test_upgrade_refreshes_a_doc_whose_content_changed(upgraded):
    """A doc that already exists must be updated, not left at the old text."""
    home = upgraded
    for rel in ("prereqs.md", "tools/berry.md"):
            got = (home / ".claude" / "docs" / rel).read_text()
            assert "OLD CONTENT" not in got, f"{rel} was not refreshed by the upgrade"
            assert got == (REPO / "docs" / rel).read_text(), f"{rel} does not match the kit"


def test_every_doc_claude_md_points_at_is_installed_by_upgrade(upgraded):
    """No dangling pointer on an upgraded machine."""
    home = upgraded
    claude_md = (home / ".claude" / "CLAUDE.md").read_text()
    dst = home / ".claude" / "docs"
    named = set(re.findall(r"~/\.claude/docs/([\w./-]+\.md)", claude_md))
    assert named, "CLAUDE.md names no docs; this test would assert nothing"
    missing = sorted(n for n in named if not (dst / n).exists())
    assert not missing, f"CLAUDE.md points at docs the upgrade did not install: {missing}"
