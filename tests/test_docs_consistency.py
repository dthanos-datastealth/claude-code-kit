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


def test_documented_marketplace_adds_use_the_shorthand_form():
    """Every `claude plugin marketplace add` we tell a user to run must use the
    `owner/repo[@ref]` shorthand.

    `claude/settings.json` declares each marketplace as a `github` source, and
    Claude Code refuses an add whose source kind differs from the declaration
    for that name. Verified against the real CLI:

        $ claude plugin marketplace add https://github.com/…/hallbayes.git#prerelease
        ✘ Failed to add marketplace: Cannot add marketplace "berry-marketplace":
          its network source differs from the one declared for it in settings

    while `dthanos-datastealth/hallbayes@prerelease` is accepted and resolves
    the right ref. A doc that drifts back to the URL form hands testers a
    command that cannot work.
    """
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    offenders = []
    for md in sorted(repo.glob("docs/**/*.md")) + [repo / "README.md"]:
        for i, line in enumerate(md.read_text().splitlines(), 1):
            m = re.search(r"marketplace add\s+(\S+)", line)
            if not m:
                continue
            spec = m.group(1).strip("`\"'")
            if spec.startswith(("http://", "https://", "git@")):
                offenders.append(f"{md.relative_to(repo)}:{i}: {spec}")
    assert not offenders, (
        "URL-form marketplace add in user-facing docs; the CLI rejects it "
        "against a github-declared source:\n  " + "\n  ".join(offenders)
    )


def test_readme_test_count_matches_the_suite():
    """The README states how many pytest cases the kit ships.

    Stale counts are a recorded past finding here (README claimed 21 plugins /
    23 docs / 36 tests long after all three had moved). A number nobody checks
    is a number that drifts, so this asserts it. If you added or removed tests,
    update the two README occurrences — that is the whole fix.
    """
    import re
    import subprocess
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    out = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-q", "--collect-only"],
        cwd=repo, capture_output=True, text=True,
    ).stdout
    m = re.search(r"^(\d+) tests collected", out, re.M) or re.search(r"(\d+) tests? collected", out)
    assert m, f"could not read collected count from pytest output:\n{out[-500:]}"
    actual = int(m.group(1))

    stated = {int(n) for n in re.findall(r"(\d+) pytest cases", (repo / "README.md").read_text())}
    assert stated, "README no longer states a pytest case count"
    assert stated == {actual}, (
        f"README says {sorted(stated)} pytest cases; the suite collects {actual}"
    )
