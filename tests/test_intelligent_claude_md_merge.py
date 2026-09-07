"""Tests for scripts/intelligent-claude-md-merge.py — heading-based CLAUDE.md
merge with 3-way conflict detection per the kit manifest."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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


PREVIOUS_RELEASE = REPO / "tests" / "fixtures" / "previous-release-CLAUDE.md"


@pytest.fixture(scope="module")
def upgrade_baseline():
    """The template stable users actually have, and the one they are moving to.

    Read from a committed fixture, NOT from git history. Deriving it with
    `git log -2 -- claude/CLAUDE.md` was tried and is a trap: mid-release it
    resolves to an earlier commit of the release being developed, so nothing
    differs, both guards below pass with nothing asserted, and the window
    shrinks with every further commit to the file. A fixture also removes the
    shallow-clone skip.
    """
    assert PREVIOUS_RELEASE.is_file(), (
        f"missing {PREVIOUS_RELEASE}; see tests/fixtures/README.md")
    prev = PREVIOUS_RELEASE.read_text()
    template = (REPO / "claude" / "CLAUDE.md").read_text()
    assert prev != template, (
        "the baseline fixture is identical to the current template, so the "
        "upgrade guards assert nothing. It must hold the PREVIOUS release — "
        "refresh it when promoting, not while developing."
    )
    return prev, template


def _headings(text):
    import re
    return [ln for ln in text.splitlines() if re.match(r"^#{1,6} ", ln)]


def test_real_upgrade_leaves_no_heading_the_kit_removed(tmp_path, upgrade_baseline):
    """Every heading the kit dropped must be gone from the user's file.

    The synthetic cases above cover one removal at one depth. This covers the
    shipped template, at every depth, against the real manifest — which is where
    the gap was: `matches_owned` compares depth exactly, so a `###` tombstone
    does not cover a `####` beneath it. Nineteen headings went when the plugin
    catalogue became a table; eighteen were removed and the depth-4 spec-kit
    playbook stayed behind, carrying 31 orphaned lines into every upgraded file.

    Any future removal that forgets a tombstone fails here. The message names
    the heading, which is why this is kept alongside the byte-identity guard.
    """
    prev_text, template = upgrade_baseline
    kit_new, user, prev = tmp_path / "new.md", tmp_path / "user.md", tmp_path / "prev.md"
    kit_new.write_text(template)
    prev.write_text(prev_text)
    user.write_text(prev_text)

    res = _run(kit_new, user, prev=prev)
    assert res.returncode == 0, res.stderr

    before, after = _headings(prev_text), _headings(template)
    merged = _headings(user.read_text())
    dropped = [h for h in before if h not in after]
    assert dropped, "the baseline drops no heading; it cannot detect a missing tombstone"
    stale = [h for h in dropped if h in merged]
    assert not stale, (
        "the kit removed these headings but they survived the upgrade; add a "
        "tombstone to claude/CLAUDE.md.manifest.json at the heading's own depth:\n  "
        + "\n  ".join(stale)
    )


def test_real_upgrade_delivers_the_new_template_content(tmp_path, upgrade_baseline):
    """A user who changed nothing must end up with exactly the new template.

    Byte-identity is both directions at once: nothing retired survives, nothing
    new is dropped, nothing is reordered. It is the right invariant only for the
    UNMODIFIED user — a user who edited a kit section must keep their edits, and
    the conflict tests above cover that.
    """
    prev_text, template = upgrade_baseline
    kit_new, user, prev = tmp_path / "new.md", tmp_path / "user.md", tmp_path / "prev.md"
    kit_new.write_text(template)
    prev.write_text(prev_text)
    user.write_text(prev_text)

    res = _run(kit_new, user, prev=prev)
    assert res.returncode == 0, res.stderr
    merged = user.read_text()

    if merged != template:
        import difflib
        diff = "\n".join(list(difflib.unified_diff(
            template.splitlines(), merged.splitlines(),
            "kit template", "what the user gets", lineterm="", n=1))[:40])
        raise AssertionError(
            "a clean upgrade did not reproduce the shipped template. Lines only "
            "in the template were dropped (their section is not manifest-owned); "
            "lines only in the result are stale (their section needs a "
            f"tombstone):\n{diff}"
        )


def _load_merger():
    import importlib.util
    repo = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "merger", repo / "scripts" / "intelligent-claude-md-merge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_heading_in_the_shipped_template_is_kit_owned():
    """A heading the manifest does not list is treated as the USER's, so an
    upgrade preserves their old copy and never delivers the kit's new one.

    This is the silent direction of the same mechanism the removal tests cover.
    Fourteen headings were unlisted — including both agent protocols and all of
    Berry's operational rules — so a clean upgrade kept the previous release's
    text for every one of them. The rules this release exists to ship reached
    nobody who upgraded.

    Every `##`-and-deeper heading the kit ships must be listed. The H1 is the
    document title and is not a section.
    """
    import json
    import re

    repo = Path(__file__).resolve().parents[1]
    merger = _load_merger()
    owned = json.loads((repo / "claude" / "CLAUDE.md.manifest.json").read_text())["owned_sections"]

    unowned = []
    for line in (repo / "claude" / "CLAUDE.md").read_text().splitlines():
        m = re.match(r"^(#{2,6})\s+\S", line)
        if not m:
            continue
        if merger.matches_owned(line, len(m.group(1)), owned) is None:
            unowned.append(line)

    assert not unowned, (
        "these headings ship in claude/CLAUDE.md but the manifest does not own "
        "them, so an upgrade will keep the user's old text instead of yours. "
        "Add an entry at each heading's own depth:\n  " + "\n  ".join(unowned)
    )


def test_no_heading_matches_more_than_one_manifest_entry():
    """Ownership must be unambiguous.

    The merger matches on depth and heading text only — it never reads the
    manifest's `parent` field, so that field cannot scope a prefix rule. As
    generic prefixes accumulate (`#### Hard rules`, `#### Verifier backend`),
    two entries could match one heading and which wins would depend on entry
    order. Today none do, and this keeps it that way.
    """
    import json
    import re

    merger = _load_merger()
    owned = json.loads((REPO / "claude" / "CLAUDE.md.manifest.json").read_text())["owned_sections"]

    ambiguous = []
    for line in (REPO / "claude" / "CLAUDE.md").read_text().splitlines():
        m = re.match(r"^(#{2,6})\s+\S", line)
        if not m:
            continue
        depth = len(m.group(1))
        hits = [e["heading"] for e in owned
                if merger.matches_owned(line, depth, [e]) is not None]
        if len(hits) > 1:
            ambiguous.append(f"{line}  <- matched by {hits}")
    assert not ambiguous, (
        "a heading is claimed by more than one manifest entry; which one wins "
        "depends on entry order:\n  " + "\n  ".join(ambiguous)
    )


def test_manifest_parent_fields_name_real_sections():
    """`parent` is documentation, so it must at least be true."""
    import json

    manifest = json.loads((REPO / "claude" / "CLAUDE.md.manifest.json").read_text())
    body = (REPO / "claude" / "CLAUDE.md").read_text()
    wrong = [e["heading"] for e in manifest["owned_sections"]
             if e.get("parent") and e["parent"] not in body]
    assert not wrong, (
        "these entries name a parent section that is not in the template:\n  "
        + "\n  ".join(wrong))
