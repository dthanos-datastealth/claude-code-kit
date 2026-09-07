"""Tests for scripts/intelligent-claude-md-merge.py — heading-based CLAUDE.md
merge with 3-way conflict detection per the kit manifest."""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MERGER = REPO / "scripts" / "intelligent-claude-md-merge.py"
MANIFEST = REPO / "claude" / "CLAUDE.md.manifest.json"
KIT_CLAUDE_MD = REPO / "claude" / "CLAUDE.md"


def _run(kit: Path, user: Path, prev: Path | None = None, manifest: Path = MANIFEST,
         conflict_dir: Path | None = None, mode: str = "apply",
         input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run the merger; return CompletedProcess."""
    args = ["python3", str(MERGER), str(kit), str(user),
            "--manifest", str(manifest), "--mode", mode]
    if prev is not None:
        args += ["--prev", str(prev)]
    if conflict_dir is not None:
        args += ["--conflict-dir", str(conflict_dir)]
    return subprocess.run(args, text=True, capture_output=True, input=input_text)


def _write(path: Path, content: str) -> None:
    path.write_text(content)


# ---------- Test cases ----------

KIT_PREV = """\
# Global Claude Code Configuration

## Core Principles
- Be concise.
- Evidence before assertions.

---

## Memory System
Persistent memory at ~/.claude/projects/<encoded>/memory/.
"""

KIT_NEW = """\
# Global Claude Code Configuration

## Core Principles
- Be concise.
- Evidence before assertions.
- NEW: NEVER speculate without evidence.

---

## Memory System
Persistent memory at ~/.claude/projects/<encoded>/memory/.

> Note: path encoding uses dashes.
"""


def test_case_5_user_edited_kit_section_conflict_surfaced(tmp_path):
    """Case 5/9: user modified a kit-owned section AND kit changed it differently → CONFLICT."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    conflict_dir = tmp_path / "conflicts"

    # User has modified "## Core Principles" differently from kit's new version
    user.write_text(KIT_PREV.replace("Evidence before assertions.",
                                      "Evidence before assertions.\n- MY EXTRA RULE."))
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)

    r = _run(kit, user, prev=prev, conflict_dir=conflict_dir, mode="apply", input_text="a\n")
    # Mode "apply" with [a]=abort on conflict → returncode != 0, no write
    assert r.returncode != 0, f"abort path should exit non-zero; got rc={r.returncode}, stderr={r.stderr}"
    assert "CONFLICT" in r.stdout or "CONFLICT" in r.stderr, "conflict not surfaced"


def test_case_7_user_unchanged_kit_advanced_clean_apply(tmp_path):
    """Case 7: live unchanged from kit_prev + kit advanced → clean kit_new applied."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    user.write_text(KIT_PREV)
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)
    r = _run(kit, user, prev=prev, mode="apply")
    assert r.returncode == 0, f"clean apply failed: {r.stderr}"
    merged = user.read_text()
    assert "NEW: NEVER speculate without evidence." in merged
    assert "path encoding uses dashes." in merged


def test_case_8_user_modified_kit_unchanged_preserved(tmp_path):
    """Case 8: live modified + kit didn't change this section → keep live (no conflict)."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    # User added a custom bullet to Core Principles; kit_new = kit_prev for this section
    user.write_text(KIT_PREV.replace("Evidence before assertions.",
                                      "Evidence before assertions.\n- MY CUSTOM."))
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_PREV)  # kit unchanged for Core Principles
    r = _run(kit, user, prev=prev, mode="apply")
    assert r.returncode == 0, f"expected clean apply (no conflict): {r.stderr}"
    assert "MY CUSTOM." in user.read_text(), "user customization lost"


def test_case_10_conflict_m_writes_conflict_file(tmp_path):
    """Case 10: conflict → choose [m] → writes side-by-side conflict file + skips section."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    conflict_dir = tmp_path / "conflicts"

    user.write_text(KIT_PREV.replace("Evidence before assertions.",
                                      "Evidence before assertions.\n- MY EXTRA."))
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)

    r = _run(kit, user, prev=prev, conflict_dir=conflict_dir, mode="apply", input_text="m\n")
    assert r.returncode == 0, f"[m] path should succeed: {r.stderr}"
    # Conflict file should exist
    conflicts = list(conflict_dir.glob("*.conflict.md"))
    assert len(conflicts) >= 1, f"no conflict file in {conflict_dir}"
    content = conflicts[0].read_text()
    assert "<<<<<<<" in content and "=======" in content and ">>>>>>>" in content


def test_case_11_unresolved_conflict_blocks_upgrade(tmp_path):
    """Case 11: pre-existing unresolved conflict file blocks new upgrade."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    conflict_dir = tmp_path / "conflicts"
    conflict_dir.mkdir()
    # Plant an unresolved conflict file
    (conflict_dir / "CLAUDE.md-foo.conflict.md").write_text("unresolved")
    user.write_text(KIT_PREV)
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)

    r = _run(kit, user, prev=prev, conflict_dir=conflict_dir, mode="apply")
    assert r.returncode != 0, "should refuse upgrade when conflict dir non-empty"
    assert "unresolved" in r.stderr.lower() or "conflict" in r.stderr.lower()


def test_case_12_status_lists_unresolved_conflicts(tmp_path):
    """Case 12: --mode status returns list of unresolved conflicts."""
    conflict_dir = tmp_path / "conflicts"
    conflict_dir.mkdir()
    (conflict_dir / "CLAUDE.md-bar.conflict.md").write_text("x")
    (conflict_dir / "CLAUDE.md-baz.conflict.md").write_text("y")
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    user.write_text(KIT_PREV)
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)
    r = _run(kit, user, prev=prev, conflict_dir=conflict_dir, mode="status")
    assert r.returncode == 0, f"status mode failed: {r.stderr}"
    assert "CLAUDE.md-bar" in r.stdout and "CLAUDE.md-baz" in r.stdout


def test_user_only_section_preserved(tmp_path):
    """Section not in manifest (e.g., user's ### Sourcegraph block) is kept verbatim."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    # User has a totally-non-kit section in between kit sections
    user.write_text("""# Global Claude Code Configuration

## Core Principles
- Be concise.
- Evidence before assertions.

---

### My Custom Section
This is mine and not in the manifest.

---

## Memory System
Persistent memory at ~/.claude/projects/<encoded>/memory/.
""")
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)
    r = _run(kit, user, prev=prev, mode="apply")
    assert r.returncode == 0, f"apply failed: {r.stderr}"
    merged = user.read_text()
    assert "### My Custom Section" in merged, "user-only section lost"
    assert "This is mine and not in the manifest." in merged


def test_dry_run_does_not_write(tmp_path):
    """--mode dry-run prints proposed changes but doesn't modify the file."""
    user = tmp_path / "CLAUDE.md"
    prev = tmp_path / "kit-prev.md"
    kit = tmp_path / "kit-new.md"
    original = KIT_PREV
    user.write_text(original)
    prev.write_text(KIT_PREV)
    kit.write_text(KIT_NEW)
    r = _run(kit, user, prev=prev, mode="dry-run")
    assert r.returncode == 0
    assert user.read_text() == original, "dry-run modified the file"


# ---------- Kit-owned section REMOVAL ----------
#
# When the kit drops a section it used to own (e.g. the per-plugin `###`
# subsections collapsed into one table), the merger must remove it from the
# user's file. Leaving it behind produces the worst outcome: the new guidance
# AND the stale guidance it replaced, side by side and contradictory.
#
# The manifest keeps listing removed headings deliberately — the entry is what
# marks the section kit-owned, and therefore removable. Drop the entry and the
# section becomes user-owned and is preserved forever.

_REMOVE_PREV = """\
# Global Claude Code Configuration

## Installed Plugins & When to Use Them
Preamble, old.

### Playwright
Old Playwright guidance.

### Berry (Evidence Verification)
Berry rules.
"""

_REMOVE_NEW = """\
# Global Claude Code Configuration

## Installed Plugins & When to Use Them
Preamble, new, with a table.

### Berry (Evidence Verification)
Berry rules.
"""


def test_removed_kit_section_is_deleted_when_user_did_not_modify_it(tmp_path):
    """Kit drops `### Playwright`; user never touched it → it must disappear."""
    kit, user, prev = tmp_path / "kit.md", tmp_path / "user.md", tmp_path / "prev.md"
    _write(kit, _REMOVE_NEW)
    _write(prev, _REMOVE_PREV)
    _write(user, _REMOVE_PREV)  # live == kit_prev: a clean, unmodified upgrade

    res = _run(kit, user, prev=prev)
    assert res.returncode == 0, res.stderr
    merged = user.read_text()

    assert "### Playwright" not in merged, (
        "kit-owned section removed from the template survived the upgrade:\n" + merged
    )
    assert "Old Playwright guidance." not in merged
    # The surviving sections are untouched.
    assert "### Berry (Evidence Verification)" in merged
    assert "Preamble, new, with a table." in merged


def test_removed_kit_section_that_user_modified_is_not_silently_deleted(tmp_path):
    """User customized a section the kit later dropped → never silently discard it."""
    kit, user, prev = tmp_path / "kit.md", tmp_path / "user.md", tmp_path / "prev.md"
    conflict_dir = tmp_path / "conflicts"
    _write(kit, _REMOVE_NEW)
    _write(prev, _REMOVE_PREV)
    _write(user, _REMOVE_PREV.replace("Old Playwright guidance.",
                                      "MY OWN Playwright notes."))

    res = _run(kit, user, prev=prev, conflict_dir=conflict_dir)
    assert res.returncode != 0 or "MY OWN Playwright notes." in user.read_text(), (
        "user's own edits to a kit-dropped section were discarded without a conflict"
    )
