from tests.helpers import run_install


def test_backup_created_when_claude_md_exists():
    r = run_install(preexisting_claude_md="# old content\n")
    backups = list((r.home / ".claude" / "backups").glob("*/CLAUDE.md"))
    assert len(backups) == 1, f"expected 1 backup, found {backups}"
    assert backups[0].read_text() == "# old content\n"


def test_backup_created_when_settings_json_exists():
    r = run_install(preexisting_settings='{"env": {"FOO": "bar"}}')
    backups = list((r.home / ".claude" / "backups").glob("*/settings.json"))
    assert len(backups) == 1
    assert '"FOO": "bar"' in backups[0].read_text()


def test_no_backup_when_no_preexisting_files():
    r = run_install()
    backup_root = r.home / ".claude" / "backups"
    if backup_root.exists():
        assert not any(backup_root.iterdir()), "backup dir should be empty"
