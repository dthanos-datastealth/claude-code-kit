"""What install.sh puts in ~/.claude, and on which CLI.

The kit's instructions reach Claude one way or the other, never both. On a CLI
that supports ~/.claude/rules they ship as rule files. Below the floor that
directory is ignored, so the CLAUDE.md template is the only thing that works.
"""
from tests.helpers import run_install

LEGACY = {"CCK_FAKE_CLAUDE_VERSION": "2.0.63"}


def test_legacy_cli_gets_the_claude_md_template():
    r = run_install(extra_env=LEGACY)
    content = (r.home / ".claude" / "CLAUDE.md").read_text()
    assert "MANDATORY" in content or "Core Principles" in content, \
        "copied CLAUDE.md does not look like the kit template"


def test_legacy_cli_backs_up_before_overwriting():
    """Replacing the user's file is only acceptable because it is recoverable."""
    r = run_install(preexisting_claude_md="# old\n", extra_env=LEGACY)
    dst = r.home / ".claude" / "CLAUDE.md"
    assert dst.read_text() != "# old\n", "old content should have been replaced"
    backups = list((r.home / ".claude" / "backups").glob("*/CLAUDE.md"))
    assert len(backups) == 1, "old content should have been backed up first"
    assert backups[0].read_text() == "# old\n", "the backup is not the user's file"


def test_supported_cli_does_not_write_claude_md_at_all():
    r = run_install(preexisting_claude_md="# mine\n")
    assert (r.home / ".claude" / "CLAUDE.md").read_text() == "# mine\n", \
        "the kit wrote CLAUDE.md on a CLI where it ships rules instead"
