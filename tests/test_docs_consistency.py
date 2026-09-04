"""Cross-document consistency checks for claims that drift.

These are content assertions, not a lint: they live in the suite CI already
runs, and they cost nothing to keep.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The dual-graph MCP is an unbundled external prerequisite the user registers
# with `claude mcp add`; install.sh contains no `mcp add` at all. philosophy.md
# claimed it "is registered automatically" for several releases, because a
# reframe updated the README and prereqs.md and left this file behind. Any doc
# that tells a reader registration is automatic sends them past the one step
# that makes the kit's first mandatory search tool exist.
AUTO_REGISTRATION_CLAIM = re.compile(
    r"dual.graph.{0,120}?(?:registered|installed|configured)\s+automatically",
    re.IGNORECASE | re.DOTALL,
)

CHECKED_DOCS = ("docs/philosophy.md", "docs/prereqs.md", "README.md", "claude/CLAUDE.md")


def test_no_doc_claims_the_dual_graph_mcp_is_registered_automatically():
    offenders = []
    for rel in CHECKED_DOCS:
        text = (REPO / rel).read_text()
        for m in AUTO_REGISTRATION_CLAIM.finditer(text):
            line = text[: m.start()].count("\n") + 1
            offenders.append(f"{rel}:{line}: {m.group(0)[:90]!r}")
    assert not offenders, (
        "install.sh never registers an MCP server; these read as if it does:\n"
        + "\n".join(offenders)
    )


def test_install_sh_really_does_not_register_an_mcp_server():
    """The premise the assertion above rests on, kept honest."""
    install_sh = (REPO / "install.sh").read_text()
    assert "mcp add" not in install_sh
    assert "mcpServers" not in install_sh
