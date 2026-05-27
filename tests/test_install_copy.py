from tests.helpers import run_install


def test_claude_md_copied_to_home():
    r = run_install()
    dst = r.home / ".claude" / "CLAUDE.md"
    assert dst.exists()
    # Template ships with the scrubbed content from claude/CLAUDE.md
    content = dst.read_text()
    assert "MANDATORY" in content or "Core Principles" in content, \
        "copied CLAUDE.md does not look like the kit template"


def test_claude_md_copy_overwrites_after_backup():
    r = run_install(preexisting_claude_md="# old\n")
    dst = r.home / ".claude" / "CLAUDE.md"
    assert dst.read_text() != "# old\n", "old content should have been replaced"
    backups = list((r.home / ".claude" / "backups").glob("*/CLAUDE.md"))
    assert len(backups) == 1, "old content should have been backed up first"
