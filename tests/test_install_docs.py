"""Verify install.sh copies kit reference docs into ~/.claude/docs/."""
import re
from pathlib import Path

from tests.helpers import run_install

REPO = Path(__file__).resolve().parents[1]


def _top_level_docs() -> list[str]:
    """The TOP_LEVEL_DOCS array from install.sh.

    Read from the installer rather than restated here: a hardcoded copy silently
    stops testing whatever the installer gains next.
    """
    body = (REPO / "install.sh").read_text()
    block = re.search(r"^TOP_LEVEL_DOCS=\((.*?)^\)", body, re.S | re.M)
    assert block, "TOP_LEVEL_DOCS array not found in install.sh"
    names = re.findall(r'"([^"]+)"', block.group(1))
    assert names, "TOP_LEVEL_DOCS parsed as empty"
    return names


def test_top_level_docs_copied():
    docs = _top_level_docs()
    r = run_install()
    dst = r.home / ".claude" / "docs"
    assert dst.exists(), "docs dir should exist after install"
    for f in docs:
        assert (REPO / "docs" / f).exists(), f"{f} is listed in install.sh but missing from docs/"
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


def test_per_tool_docs_copied():
    r = run_install()
    tools_dst = r.home / ".claude" / "docs" / "tools"
    assert tools_dst.exists(), "docs/tools dir should exist"
    # Spot-check a few that must be present (we ship 23 total)
    for f in (
        "berry.md",
        "spec-kit.md",
        "jdtls-lsp.md",
        "caveman.md",
        "dual-graph-mcp.md",
    ):
        assert (tools_dst / f).exists(), f"{f} should be installed at ~/.claude/docs/tools/"


def test_docs_count_matches_kit_repo():
    r = run_install()
    tools_dst = r.home / ".claude" / "docs" / "tools"
    from pathlib import Path
    repo_tools = Path(__file__).resolve().parents[1] / "docs" / "tools"
    repo_files = sorted(p.name for p in repo_tools.glob("*.md"))
    dst_files = sorted(p.name for p in tools_dst.glob("*.md"))
    assert dst_files == repo_files, (
        f"docs/tools/ count mismatch: kit has {len(repo_files)} files "
        f"({repo_files}), installed has {len(dst_files)} ({dst_files})"
    )
