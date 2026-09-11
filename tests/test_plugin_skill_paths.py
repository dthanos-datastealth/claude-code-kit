"""Plugin skills must not invoke scripts by a working-directory-relative path.

A slash command runs in whatever project the user is in. Three of these skills
drive `scripts/upgrade.sh`, which lives in the kit **checkout** rather than in
the plugin, and one drives a script that ships inside the plugin. All four
originally said things like `bash scripts/upgrade.sh --status`, which resolves
only when the user's working directory happens to be the clone.

Testing the underlying scripts from the repo hid this completely: the scripts
were correct, the path to them was not. Invoking `/claude-code-kit:status` from
any real project produced `bash: scripts/upgrade.sh: No such file or directory`.
"""
from __future__ import annotations

import re

from tests.helpers import REPO

SKILLS = sorted((REPO / "plugins" / "claude-code-kit" / "skills").glob("*/SKILL.md"))

# A fenced command line that starts a relative path into a scripts/ directory.
RELATIVE_INVOCATION = re.compile(
    r"^\s*(?:bash|sh|python3)\s+(?!\"?\$)(?:\./)?(?:scripts|plugins)/", re.MULTILINE
)


def test_there_are_skills_to_check():
    """Guards the glob: an empty SKILLS list would make every test below
    pass while checking nothing."""
    assert SKILLS, "no SKILL.md files found — the glob is wrong"


def test_no_skill_invokes_a_script_by_relative_path():
    offenders = []
    for skill in SKILLS:
        text = skill.read_text()
        for m in RELATIVE_INVOCATION.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            line = text.splitlines()[line_no - 1].strip()
            offenders.append(f"{skill.parent.name}:{line_no}: {line}")
    assert not offenders, (
        "these resolve against the user's working directory, not the kit:\n  "
        + "\n  ".join(offenders)
        + "\n\nUse ${CLAUDE_PLUGIN_ROOT} for scripts inside the plugin, or the "
          "repo_dir recorded in ~/.claude/.kit-version for scripts in the checkout."
    )


def test_checkout_driving_skills_resolve_the_repo_dir():
    """The three skills that drive scripts/upgrade.sh must read repo_dir."""
    for name in ("status", "upgrade", "rollback"):
        text = (REPO / "plugins" / "claude-code-kit" / "skills" / name /
                "SKILL.md").read_text()
        assert "repo_dir" in text, (
            f"{name} drives a script in the checkout but never resolves its "
            "location"
        )


def test_install_records_the_repo_dir():
    """repo_dir is what makes the above possible, so the writer must emit it."""
    backup_sh = (REPO / "scripts" / "_kit_backup.sh").read_text()
    assert '"repo_dir"' in backup_sh, (
        "kit_write_version_marker must record repo_dir in ~/.claude/.kit-version"
    )
