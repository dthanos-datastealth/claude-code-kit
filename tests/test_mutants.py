"""The mutant catalogue must stay honest.

`scripts/mutate.py run-all` is the real check and is too slow for every suite
run — it copies the tree and runs a test selection per mutant. What IS cheap,
and what actually rots, is the catalogue: a `find` string that no longer
matches means the code moved and the mutant has been silently asserting
nothing since.

That is the same defect class mutation testing exists to catch, one level up,
so it is worth a fast test rather than trust.
"""
from __future__ import annotations

import json

from tests.helpers import REPO

MUTANTS = REPO / "scripts" / "mutants.json"
KNOWN_KEYS = {"id", "file", "find", "replace", "tests", "breaks", "history"}


def _mutants() -> list[dict]:
    return json.loads(MUTANTS.read_text())["mutants"]


def test_every_mutant_anchor_still_matches_exactly_once():
    """The find-string must appear exactly once in its target file.

    Zero matches: the mutant is stale and has been testing nothing.
    Two or more: it would mutate more than one site, so a kill tells you
    nothing about which.
    """
    problems = []
    for m in _mutants():
        target = REPO / m["file"]
        if not target.is_file():
            problems.append(f"{m['id']}: {m['file']} does not exist")
            continue
        count = target.read_text().count(m["find"])
        if count != 1:
            problems.append(
                f"{m['id']}: anchor appears {count}x in {m['file']} "
                f"(expected exactly 1) — {m['find'][:60]!r}"
            )
    assert not problems, "stale or ambiguous mutants:\n  " + "\n  ".join(problems)


def test_every_mutant_actually_changes_the_file():
    """A mutant whose replacement equals its anchor is a no-op that always
    'survives' or always 'dies' for the wrong reason."""
    same = [m["id"] for m in _mutants() if m["find"] == m["replace"]]
    assert not same, f"mutants that change nothing: {same}"


def test_every_mutant_names_tests_that_exist():
    missing = []
    for m in _mutants():
        for rel in m["tests"]:
            if not (REPO / rel).is_file():
                missing.append(f"{m['id']} -> {rel}")
    assert not missing, f"mutants naming non-existent tests: {missing}"


def test_every_mutant_explains_what_it_breaks():
    """The `breaks` line is what makes a surviving mutant actionable — it
    states the defect a reader is being told nobody would notice."""
    thin = [
        m["id"] for m in _mutants()
        if len(m.get("breaks", "")) < 40
    ]
    assert not thin, f"mutants without a usable `breaks` description: {thin}"


def test_mutant_ids_are_unique():
    ids = [m["id"] for m in _mutants()]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"duplicate mutant ids: {dupes}"


def test_no_unknown_keys():
    """Catches a typo'd key silently doing nothing — `test` for `tests`
    would leave the mutant running the whole suite."""
    problems = []
    for m in _mutants():
        for key in m:
            if key not in KNOWN_KEYS:
                problems.append(f"{m['id']}: unknown key {key!r}")
    assert not problems, problems


def test_the_files_most_likely_to_regress_are_covered():
    """Every file whose breakage caused a documented finding must have at
    least one mutant. Without this the catalogue quietly stops keeping pace
    with the code it is supposed to guard."""
    covered = {m["file"] for m in _mutants()}
    required = {
        "scripts/_kit_env.sh",
        "uninstall.sh",
        "install.sh",
        "scripts/diff-settings.py",
        "scripts/verify-install.py",
        "scripts/_kit_backup.sh",
        "scripts/intelligent-claude-md-merge.py",
        "plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh",
    }
    assert required <= covered, f"no mutant covers: {sorted(required - covered)}"
