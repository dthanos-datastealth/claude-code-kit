"""Verify install.sh copies kit reference docs into ~/.claude/docs/."""
from tests.helpers import run_install


def test_top_level_docs_copied():
    r = run_install()
    dst = r.home / ".claude" / "docs"
    assert dst.exists(), "docs dir should exist after install"
    for f in (
        "philosophy.md",
        "workflow.md",
        "prereqs.md",
        "corporate-tls.md",
        "memory-system.md",
    ):
        assert (dst / f).exists(), f"{f} should be installed at ~/.claude/docs/"


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
