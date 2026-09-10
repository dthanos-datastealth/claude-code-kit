"""On a CLI that supports ~/.claude/rules, install must not write CLAUDE.md.

Shipping both would put the same instructions in front of Claude twice, every
session, and would replace a file the kit has promised to leave alone. Below the
floor the CLAUDE.md copy is the only thing that works, so that path stays.
"""
import subprocess
from pathlib import Path

from tests.helpers import run_install

REPO = Path(__file__).resolve().parents[1]


def test_supported_cli_leaves_the_users_claude_md_alone():
    r = run_install(preexisting_claude_md="# mine\n\n- always use tabs\n")
    live = (r.home / ".claude" / "CLAUDE.md").read_text()
    assert "always use tabs" in live, (
        "install replaced the user's CLAUDE.md on a CLI where the kit ships rules")


def test_supported_cli_installs_rules():
    r = run_install()
    rules = r.home / ".claude" / "rules"
    assert (rules / "10-kit-core.md").is_file(), "rules not installed"


def test_supported_cli_does_not_ship_instructions_twice():
    """The same rule must not arrive in both CLAUDE.md and rules/."""
    r = run_install()
    claude_md = r.home / ".claude" / "CLAUDE.md"
    probe = "Dual-graph MCP FIRST"
    in_rules = probe in (r.home / ".claude" / "rules" / "20-kit-code-search.md").read_text()
    in_md = claude_md.is_file() and probe in claude_md.read_text()
    assert in_rules, "the rule is missing from rules/"
    assert not in_md, "the same instruction is also in CLAUDE.md; it loads twice"


def test_below_the_floor_still_copies_claude_md():
    """Older CLIs ignore ~/.claude/rules, so the template is all they get."""
    r = run_install(extra_env={"CCK_FAKE_CLAUDE_VERSION": "2.0.63"})
    live = r.home / ".claude" / "CLAUDE.md"
    assert live.is_file(), "the legacy path must still install the template"
    assert "MANDATORY" in live.read_text()
