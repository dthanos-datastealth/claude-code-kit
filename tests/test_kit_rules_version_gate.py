"""The rules path is gated on a CLI that actually supports ~/.claude/rules.

Support landed in Claude Code 2.0.64 (10 Dec 2025). Below that the directory is
ignored, so shipping rules there would silently drop every kit instruction —
the worst possible failure, because nothing errors and the kit looks installed.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _supported(version: str | None, tmp_path: Path) -> bool:
    """Run kit_rules_supported against a fake `claude --version`."""
    fake = tmp_path / "claude"
    if version is None:
        body = "#!/usr/bin/env bash\nexit 127\n"
    else:
        body = f"#!/usr/bin/env bash\necho '{version} (Claude Code)'\n"
    fake.write_text(body)
    fake.chmod(0o755)
    script = (
        f'REPO_DIR="{REPO}"; CLAUDE_HOME="{tmp_path}/.claude"; log() {{ :; }}; err() {{ :; }};\n'
        f'. "{REPO}/scripts/_kit_rules.sh"\n'
        "kit_rules_supported && echo YES || echo NO\n"
    )
    r = subprocess.run(["bash", "-c", script],
                       env={"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)},
                       text=True, capture_output=True)
    return "YES" in r.stdout


def test_current_cli_is_supported(tmp_path):
    assert _supported("2.1.251", tmp_path)


def test_the_floor_release_is_supported(tmp_path):
    assert _supported("2.0.64", tmp_path)


def test_just_below_the_floor_is_not(tmp_path):
    assert not _supported("2.0.63", tmp_path)


def test_older_majors_are_not_supported(tmp_path):
    assert not _supported("1.9.99", tmp_path)


def test_a_much_newer_cli_is_supported(tmp_path):
    """Version compare must be numeric, not lexical: 2.0.100 > 2.0.64."""
    assert _supported("2.0.100", tmp_path)
    assert _supported("10.0.0", tmp_path)


def test_an_unusable_cli_is_not_supported(tmp_path):
    """No version means no evidence of support; fall back rather than guess."""
    assert not _supported(None, tmp_path)
