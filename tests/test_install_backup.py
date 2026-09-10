from tests.helpers import reinstall_over_existing, run_install


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


def test_backup_includes_rules_on_reinstall():
    """The kit's instructions live in rules/, not CLAUDE.md, and kit_copy_rules
    replaces all six kit files wholesale on every install and upgrade. A backup
    set that omits rules/ cannot restore the kit's actual instruction content,
    so a release shipping a bad rule would have no revert path — even though
    docs/upgrading.md offers rollback as the remedy for exactly that.

    Modelled as a re-install rather than a first install, because on a first
    install rules/ does not exist yet when the backup is taken. The second run
    is also the one that matters: it is the upgrade-shaped case, where there
    is existing content to lose.
    """
    r = reinstall_over_existing(extra_rule=("99-mine.md", "# mine\n"))
    backups = r.home / ".claude" / "backups"
    assert list(backups.glob("*/rules/10-kit-core.md")), (
        "kit rule files must be captured; found "
        f"{sorted(p.name for p in backups.glob('*/*'))}"
    )
    assert list(backups.glob("*/rules/99-mine.md")), (
        "a user-authored rule file must be captured — it is the part the user "
        "cannot recreate from the repository"
    )
