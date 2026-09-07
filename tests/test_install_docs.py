"""Verify install.sh copies kit reference docs into ~/.claude/docs/."""
import re
from pathlib import Path

import pytest

from tests.helpers import run_install

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def installed():
    """One install for the whole module.

    Three tests here each ran their own `install.sh` with identical arguments
    and only read from the result — about 2.4s of repeating work the first call
    had already done. Nothing in this module mutates the installed tree, so one
    install serves all three.
    """
    return run_install()


def _top_level_docs() -> list[str]:
    """The TOP_LEVEL_DOCS array from scripts/_kit_docs.sh.

    Read from the installer rather than restated here: a hardcoded copy silently
    stops testing whatever the installer gains next.
    """
    body = (REPO / "scripts" / "_kit_docs.sh").read_text()
    block = re.search(r"^TOP_LEVEL_DOCS=\((.*?)^\)", body, re.S | re.M)
    assert block, "TOP_LEVEL_DOCS array not found in scripts/_kit_docs.sh"
    names = re.findall(r'"([^"]+)"', block.group(1))
    assert names, "TOP_LEVEL_DOCS parsed as empty"
    return names


def test_top_level_docs_copied(installed):
    docs = _top_level_docs()
    dst = installed.home / ".claude" / "docs"
    assert dst.exists(), "docs dir should exist after install"
    for f in docs:
        assert (REPO / "docs" / f).exists(), f"{f} is listed in _kit_docs.sh but missing from docs/"
        assert (dst / f).exists(), f"{f} should be installed at ~/.claude/docs/"


def test_verification_standards_doc_is_shipped():
    """CLAUDE.md states the three verification rules in one line each and points
    here for the reasoning and the incidents behind them. A pointer to a file the
    installer does not copy is a dead reference on every installed machine."""
    assert "verification-standards.md" in _top_level_docs()
    body = (REPO / "claude" / "CLAUDE.md").read_text()
    assert "verification-standards.md" in body, (
        "CLAUDE.md no longer references verification-standards.md"
    )


def test_per_tool_docs_copied(installed):
    tools_dst = installed.home / ".claude" / "docs" / "tools"
    assert tools_dst.exists(), "docs/tools dir should exist"
    # Spot-check a few that must be present
    for f in (
        "berry.md",
        "spec-kit.md",
        "jdtls-lsp.md",
        "caveman.md",
        "dual-graph-mcp.md",
    ):
        assert (tools_dst / f).exists(), f"{f} should be installed at ~/.claude/docs/tools/"


def test_docs_count_matches_kit_repo(installed):
    tools_dst = installed.home / ".claude" / "docs" / "tools"
    repo_tools = REPO / "docs" / "tools"
    repo_files = sorted(p.name for p in repo_tools.glob("*.md"))
    dst_files = sorted(p.name for p in tools_dst.glob("*.md"))
    assert dst_files == repo_files, (
        f"docs/tools/ count mismatch: kit has {len(repo_files)} files "
        f"({repo_files}), installed has {len(dst_files)} ({dst_files})"
    )
