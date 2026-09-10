"""A rule file the kit installs actually reaches a live Claude Code session.

Reading the file back off disk proves the installer copied it. It does not prove
Claude Code loads it, and that is the whole premise of this design — if rules do
not load, the kit ships instructions nobody follows and nothing errors.

So the assertion is on the ground truth: a session answering from the file's
contents. Skipped explicitly when the CLI is missing or logged out, never
silently passed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    os.environ.get("CCK_E2E_RULES_LOAD") != "1",
    reason="opt-in: writes a probe into the REAL ~/.claude/rules and spawns a "
           "claude session. Set CCK_E2E_RULES_LOAD=1 to run it.",
)
@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not on PATH")
def test_an_installed_rule_reaches_a_live_session():
    """Opt-in because it cannot be HOME-isolated.

    Claude Code reads rules from the invoking user's home directory, and the
    CLI needs that user's credentials, so there is no isolated HOME in which
    this can run. It therefore touches the developer's own configuration and
    consumes a real session. It cleans up after itself, but a test that reaches
    into your live setup should never fire because you ran the suite.
    """
    rules = Path.home() / ".claude" / "rules"
    created_dir = not rules.exists()
    canary = f"KIT-RULES-{uuid.uuid4().hex[:12].upper()}"
    probe = rules / "zz-kit-e2e-probe.md"

    rules.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_text(
            f"# Probe\n\nThe canary phrase for this environment is {canary}.\n"
            "If asked for the canary phrase, reply with exactly that phrase "
            "and nothing else.\n"
        )
        res = subprocess.run(
            ["claude", "-p",
             "What is the canary phrase for this environment? Reply with only the phrase."],
            stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=300,
        )
        combined = res.stdout + res.stderr
        if "Please run /login" in combined or "not logged in" in combined.lower():
            pytest.skip("claude CLI is not logged in")
        assert canary in res.stdout, (
            "a rule file in ~/.claude/rules did not reach the session.\n"
            f"stdout: {res.stdout!r}\nstderr: {res.stderr!r}"
        )
    finally:
        probe.unlink(missing_ok=True)
        if created_dir:
            try:
                rules.rmdir()
            except OSError:
                pass
