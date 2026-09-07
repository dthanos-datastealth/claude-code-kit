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
                decorators = "".join(ast.dump(d) for d in node.decorator_list)
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


def test_scratch_dir_is_per_session_not_shared(tmp_path, monkeypatch):
    """Session teardown must not remove a concurrent session's directory.

    Every isolated HOME used to live under one shared `tests/.tmp` that session
    teardown removed wholesale, so the first pytest session to finish deleted
    the tree a second was still installing into. Reproduced before the fix: a
    full run with short sessions finishing underneath it reported six failures
    across four modules, none of them real.

    Asserted by running the real teardown against a planted sibling, not by
    reading conftest's source — a check on text you control is the proxy this
    kit's own verification standards forbid.
    """
    import importlib.util
    from pathlib import Path

    from tests.helpers import SESSION_TMP, TMP_ROOT

    spec = importlib.util.spec_from_file_location(
        "kit_conftest", Path(__file__).resolve().parent / "conftest.py")
    conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conftest)

    assert SESSION_TMP != TMP_ROOT, "session scratch dir must not be the shared root"
    assert TMP_ROOT in SESSION_TMP.parents, "session dir should live under the shared root"

    sibling = TMP_ROOT / "session-999999"
    (sibling / "home").mkdir(parents=True, exist_ok=True)
    marker = sibling / "home" / "CLAUDE.md"
    marker.write_text("another session is using this")
    try:
        conftest.pytest_sessionfinish(session=None, exitstatus=0)
        assert marker.exists(), (
            "teardown deleted a concurrent session's files; that is the bug"
        )
    finally:
        import shutil
        shutil.rmtree(sibling, ignore_errors=True)
        SESSION_TMP.mkdir(parents=True, exist_ok=True)



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
        # Accept the plugin's own name, or its stem with the lsp/mcp affixes
        # removed — CLAUDE.md names "lsp-gopls" as "gopls" and
        # "chrome-devtools-mcp" as "chrome-devtools".
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


def test_no_test_name_is_defined_twice_in_a_module():
    """A redefined test silently replaces the first one, and pytest says nothing.

    This happened here: a rewritten upgrade guard was added above an older copy
    of the same name, so the older, weaker version was the one that ran and the
    rewrite never executed. The count is unchanged, the suite is green, and the
    thing you thought you were testing is not tested.
    """
    import ast
    from collections import Counter
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    offenders = []
    for path in sorted((repo / "tests").glob("test_*.py")):
        names = [n.name for n in ast.walk(ast.parse(path.read_text()))
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name.startswith("test_")]
        for name, count in Counter(names).items():
            if count > 1:
                offenders.append(f"{path.name}::{name} defined {count} times")
    assert not offenders, (
        "a later definition shadows an earlier one; only the last runs:\n  "
        + "\n  ".join(offenders)
    )


def test_upgrading_doc_matches_the_actual_merge_policy():
    """`docs/upgrading.md` tabulates who wins each settings key. It must agree
    with `scripts/merge-policy.json`, or it documents a behaviour the kit does
    not have — which it did: the table still said the user won marketplace
    conflicts after the policy was changed so the kit could move its own release
    channel.
    """
    import json
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    policy = json.loads((repo / "scripts" / "merge-policy.json").read_text())["policies"]
    doc = (repo / "docs" / "upgrading.md").read_text()

    rows = dict(re.findall(r"^\| `(\w+)` \| [^|]+\| ([^|]+)\|$", doc, re.M))
    assert rows, "no settings-policy table found in docs/upgrading.md"

    mismatches = []
    for key, rule in policy.items():
        winner = rule.get("winner_on_conflict")
        if not winner or key not in rows:
            continue
        stated = rows[key].replace("*", "").strip().lower()
        if not stated.startswith(winner):
            mismatches.append(f"{key}: policy says {winner!r}, doc says {stated!r}")
    assert not mismatches, (
        "docs/upgrading.md disagrees with scripts/merge-policy.json:\n  "
        + "\n  ".join(mismatches))
