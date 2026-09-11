"""Unit tests for kit_compute_path in scripts/_kit_env.sh.

The composed PATH is persisted into ~/.claude/settings.json, where `env`
REPLACES the inherited variable for Claude Code and every hook and MCP
subprocess it spawns. A mistake here is not transient — it is written to disk
and inherited by everything, so the ordering properties are worth pinning
directly rather than inferring them from an install run.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tests.helpers import REPO

KIT_ENV = REPO / "scripts" / "_kit_env.sh"


def compute(path_value: str, tmp: Path) -> list[str]:
    """Call the real shell function with a controlled PATH; return entries."""
    script = f"""
    set -euo pipefail
    CLAUDE_HOME="{tmp}/.claude"
    log() {{ :; }}
    . "{KIT_ENV}"
    PATH="{path_value}" kit_compute_path
    """
    res = subprocess.run(["bash", "-c", script], text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    return res.stdout.split(":")


def _stub(d: Path, name: str) -> None:
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("#!/usr/bin/env bash\nexit 0\n")
    p.chmod(0o755)


def test_relative_order_of_the_inherited_path_is_preserved(tmp_path):
    """The regression that shipped: resolved tool directories were PREPENDED.

    On a stock macOS box `git` is /usr/bin/git, so prepending hoisted /usr/bin
    to the front — ahead of the python@3.12 libexec directory that
    docs/prereqs.md tells every reader to put first. The composed PATH then
    resolved python3 to the system 3.9, and that got written into
    settings.json permanently, reintroducing findings #1 and #13.

    Whatever else composition does, it must not reorder the user's PATH.
    """
    early, late = tmp_path / "early", tmp_path / "late"
    _stub(early, "python3")          # user put this first deliberately
    _stub(late, "python3")           # the older interpreter it shadows
    # MUST be a tool processed AFTER python3 in KIT_RUNTIME_TOOLS. With `git`
    # here — which is processed BEFORE python3 — a prepending implementation
    # produces byte-identical output, because python3's own prepend puts
    # `early` back in front. The first version of this test used `git` and
    # therefore passed against the exact regression it is named for.
    _stub(late, "npx")

    entries = compute(f"{early}:{late}", tmp_path)
    assert entries.index(str(early)) < entries.index(str(late)), (
        "composition reordered the inherited PATH: "
        f"{entries}"
    )


def test_the_first_python3_on_the_inherited_path_still_wins(tmp_path):
    """The property the ordering test exists to protect, stated directly.

    Same stub-choice constraint as above: the shadowing directory must hold a
    tool processed after python3, or a prepending implementation passes.
    """
    early, late = tmp_path / "early", tmp_path / "late"
    _stub(early, "python3")
    _stub(late, "python3")
    _stub(late, "npx")

    entries = compute(f"{early}:{late}", tmp_path)
    first_with_python = next(e for e in entries if (Path(e) / "python3").exists())
    assert first_with_python == str(early)


def test_system_directories_are_always_present(tmp_path):
    """`env` replaces rather than extends, so a composed PATH without
    /usr/bin and /bin leaves the session unable to run anything. The floor
    must come from the function, not from whatever PATH it happened to see."""
    only = tmp_path / "only"
    _stub(only, "git")
    entries = compute(str(only), tmp_path)
    for required in ("/usr/bin", "/bin"):
        assert required in entries, f"{required} missing from {entries}"


def test_no_duplicates(tmp_path):
    d = tmp_path / "d"
    _stub(d, "git")
    entries = compute(f"{d}:{d}:/usr/bin:/usr/bin", tmp_path)
    assert len(entries) == len(set(entries)), entries


def test_no_empty_entries(tmp_path):
    d = tmp_path / "d"
    _stub(d, "git")
    entries = compute(f"{d}::/usr/bin:", tmp_path)
    assert "" not in entries, entries


def test_never_injects_the_working_directory(tmp_path):
    """A degenerate case with teeth: `dirname` itself lives in /usr/bin. With
    a PATH that lacks it, $(dirname ...) returns empty, `cd "" && pwd`
    succeeds and yields the CURRENT directory — which would then be written
    into the persisted PATH."""
    only = tmp_path / "only"
    _stub(only, "git")
    entries = compute(str(only), tmp_path)
    cwd = str(Path.cwd())
    assert cwd not in entries, (
        f"the working directory {cwd} leaked into the composed PATH: {entries}"
    )
