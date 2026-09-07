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

    Counted by parsing the test files, not by spawning `pytest --collect-only`:
    this session has already collected those tests, so re-collecting them in a
    subprocess is work the run just did. The two agree exactly while the suite
    uses no `parametrize`, which the assertion below enforces.
    """
    import ast
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    tests_dir = repo / "tests"

    total = 0
    for path in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("test_"):
                    continue
                decorators = ast.dump(ast.Module(body=[], type_ignores=[]))
                for dec in node.decorator_list:
                    decorators += ast.dump(dec)
                assert "parametrize" not in decorators, (
                    f"{path.name}::{node.name} is parametrized; this count no "
                    "longer matches what pytest collects — switch to a "
                    "collection-based count"
                )
                total += 1
    assert total, "found no test functions to count"

    stated = {int(n) for n in re.findall(r"(\d+) pytest cases", (repo / "README.md").read_text())}
    assert stated, "README no longer states a pytest case count"
    assert stated == {total}, (
        f"README says {sorted(stated)} pytest cases; the suite defines {total}"
    )


def test_scratch_dir_is_per_session_not_shared():
    """Two pytest sessions in one checkout must not delete each other's HOMEs.

    The scratch root is shared, and session teardown removes a directory. When
    that directory was the shared root, the first session to finish wiped the
    tree the second was still installing into. Reproduced: a full run with short
    sessions finishing underneath it reported six failures across four modules,
    none of them real. Each session now owns a subdirectory and removes only
    that.
    """
    from pathlib import Path

    from tests.helpers import SESSION_TMP, TMP_ROOT

    assert SESSION_TMP != TMP_ROOT, "session scratch dir must not be the shared root"
    assert TMP_ROOT in SESSION_TMP.parents, "session dir should live under the shared root"

    conftest = (Path(__file__).resolve().parent / "conftest.py").read_text()
    assert "rmtree(SESSION_TMP" in conftest, "teardown must remove the session dir"
    assert "rmtree(TMP_ROOT" not in conftest, (
        "teardown must never rmtree the shared root — that is the bug this guards"
    )


def test_every_enabled_plugin_is_named_in_claude_md():
    """An agent reads CLAUDE.md, not settings.json, to learn what it has.

    A plugin the kit installs but never names is invisible: it ships, costs
    context, and no session knows to reach for it. The kit's own plugin was in
    exactly that state — enabled, with a depth-doc, and mentioned nowhere.
    """
    import json
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    body = (repo / "claude" / "CLAUDE.md").read_text().lower()
    enabled = json.loads((repo / "claude" / "settings.json").read_text())["enabledPlugins"]

    missing = []
    for key in enabled:
        name = key.split("@", 1)[0]
        # Accept the plugin name or the words of it (e.g. "chrome-devtools-mcp"
        # is named as "chrome-devtools-mcp"; "lsp-gopls" appears as "gopls").
        stem = name.replace("-lsp", "").replace("lsp-", "").replace("-mcp", "")
        if name not in body and stem not in body:
            missing.append(name)
    assert not missing, (
        "these plugins are enabled in settings.json but named nowhere in "
        "claude/CLAUDE.md, so no session knows they exist:\n  " + "\n  ".join(missing)
    )


def test_tool_docs_named_in_claude_md_exist():
    """CLAUDE.md points at depth-references by filename; each must resolve.

    Three rows relied on a `<name>.md` convention that three files do not
    follow — playwright-mcp.md, lsp-gopls.md, lsp-typescript.md — so an agent
    obeying the stated rule got a dead path.
    """
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    body = (repo / "claude" / "CLAUDE.md").read_text()
    named = set(re.findall(r"`([a-z0-9][\w.-]*\.md)`", body))
    tool_docs = {p.name for p in (repo / "docs" / "tools").glob("*.md")}
    top_docs = {p.name for p in (repo / "docs").glob("*.md")}

    missing = sorted(n for n in named if n not in tool_docs and n not in top_docs
                     and n not in {"CLAUDE.md", "AGENTS.md", "TRACKER.md", "MEMORY.md",
                                   "GEMINI.md", "spec.md", "plan.md", "tasks.md",
                                   "constitution.md", "README.md"})
    assert not missing, (
        "CLAUDE.md names these docs but they do not exist:\n  " + "\n  ".join(missing))
