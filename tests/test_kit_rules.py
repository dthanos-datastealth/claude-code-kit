"""The kit's instructions ship as owned rule files, not as prose merged into
the user's CLAUDE.md.

Claude Code discovers ~/.claude/rules/*.md rather than merging them, so the kit
can own these outright and replace them wholesale. That removes the whole class
of defect the manifest-driven merge produced: a heading the manifest forgot kept
the user on the previous release's rules, silently.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "claude" / "rules"

DEFERENCE = (
    "Anything in `~/.claude/rules/00-user-overrides.md` overrides this file. "
    "If the two disagree, follow the override and say which rule you are setting aside."
)

KIT_RULES = [
    "10-kit-core.md",
    "20-kit-code-search.md",
    "30-kit-quality-loop.md",
    "40-kit-tracker.md",
    "50-kit-plugins.md",
    "60-kit-workflow.md",
]


def test_every_kit_rule_file_exists_and_is_non_empty():
    for name in KIT_RULES:
        p = RULES / name
        assert p.is_file(), f"{name} missing from claude/rules/"
        assert len(p.read_text().strip()) > 200, f"{name} is a stub"


def test_every_kit_rule_defers_to_the_override_file():
    """Load order cannot express precedence: the docs say files are concatenated
    rather than overriding, and that contradictions resolve arbitrarily. So each
    rule has to say plainly which file wins."""
    for name in KIT_RULES:
        assert DEFERENCE in (RULES / name).read_text(), (
            f"{name} does not tell Claude the override file wins")


def test_the_override_file_ships_empty_of_rules():
    body = (RULES / "00-user-overrides.md").read_text()
    assert body.strip(), "override file should explain itself"
    assert DEFERENCE not in body, "the override file does not defer to itself"


def test_no_rule_is_path_scoped():
    """Every kit rule is unconditional. A stray `paths:` would make one load
    only when a matching file is opened, which is not what any of these mean."""
    for p in RULES.glob("*.md"):
        head = p.read_text().lstrip()
        if head.startswith("---"):
            front = head.split("---", 2)[1]
            assert "paths:" not in front, f"{p.name} is path-scoped; kit rules are unconditional"


def test_the_split_carries_every_mandatory_rule():
    """Splitting one file into six must not drop a rule on the floor.

    The failure this guards is silent: a section lost in the split still leaves
    a green suite and a shipped kit, and only shows up as an agent that stopped
    following a rule nobody noticed was gone.
    """
    template = (REPO / "claude" / "CLAUDE.md").read_text()
    combined = "\n".join((RULES / n).read_text() for n in KIT_RULES)

    probes = [
        "graph_continue",
        "audit_trace_budget",
        "synthetic proxy",
        "script can never confirm",
        "redundant WORK",
        "WIRE-PATH MISS",
        "TaskCreate",
        "verification-standards.md",
        "Co-Authored-By",
        "REDUNDANT EXPENSIVE CALL",
        "berry-search-and-learn",
        "3-strike rule",
    ]
    present = [p for p in probes if p in template]
    assert len(present) > 8, "probe list has drifted from the template; update it"
    missing = [p for p in present if p not in combined]
    assert not missing, f"the split dropped: {missing}"


def test_no_kit_section_heading_was_left_behind():
    """Every `##` section in the template must appear in some rule file."""
    import re

    template = (REPO / "claude" / "CLAUDE.md").read_text()
    combined = "\n".join((RULES / n).read_text() for n in KIT_RULES)
    headings = [h for h in re.findall(r"^## .+$", template, re.M)]
    assert headings, "template has no sections; this test would assert nothing"
    missing = [h for h in headings if h not in combined]
    assert not missing, f"sections in the template but in no rule file: {missing}"
