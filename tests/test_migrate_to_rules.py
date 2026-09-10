"""Migration lifts the kit's sections out of the user's CLAUDE.md and leaves
theirs exactly where they were.

This is the last job the manifest-driven merger does. After it runs, the kit
never writes ~/.claude/CLAUDE.md again.
"""
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIGRATE = REPO / "scripts" / "migrate-claude-md-to-rules.py"
MANIFEST = REPO / "claude" / "CLAUDE.md.manifest.json"
PREVIOUS = REPO / "tests" / "fixtures" / "previous-release-CLAUDE.md"

MINE = "\n## My Own Rules\n\n- always use tabs\n- never rebase a shared branch\n"


def _run(target: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(MIGRATE), str(target), "--manifest", str(MANIFEST), *extra],
        text=True, capture_output=True)


def test_kit_sections_go_and_user_sections_stay(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text(PREVIOUS.read_text() + MINE)

    res = _run(target)
    assert res.returncode == 0, res.stderr
    after = target.read_text()

    assert "## My Own Rules" in after, "the user's own section was removed"
    assert "always use tabs" in after
    assert "never rebase a shared branch" in after
    assert "## Core Principles" not in after, "a kit section survived migration"
    assert "## MANDATORY Quality Loop" not in after


def test_the_user_keeps_their_section_byte_for_byte(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text(PREVIOUS.read_text() + MINE)
    _run(target)
    assert MINE.strip() in target.read_text(), "the user's section was reflowed or reordered"


def test_a_stamp_says_where_the_kit_content_went(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text(PREVIOUS.read_text() + MINE)
    _run(target)
    head = target.read_text()
    assert "rules/" in head, "nothing tells the reader where the kit's content went"


def test_migration_is_idempotent(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_text(PREVIOUS.read_text() + MINE)
    _run(target)
    once = target.read_text()
    second = _run(target)
    assert second.returncode == 3, "second run should report nothing to do"
    assert target.read_text() == once, "second run changed the file"


def test_dry_run_writes_nothing(tmp_path):
    target = tmp_path / "CLAUDE.md"
    original = PREVIOUS.read_text()
    target.write_text(original)
    res = _run(target, "--dry-run")
    assert res.returncode == 0, res.stderr
    assert target.read_text() == original, "dry-run wrote to the file"
    assert "Core Principles" in res.stdout, "dry-run did not report what it would remove"


def test_a_file_with_no_kit_content_is_untouched(tmp_path):
    target = tmp_path / "CLAUDE.md"
    original = "# Mine\n\n## My Own Rules\n\n- always use tabs\n"
    target.write_text(original)
    res = _run(target)
    assert res.returncode == 3, res.stdout + res.stderr
    assert target.read_text() == original
