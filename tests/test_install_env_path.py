"""install.sh persists a runtime PATH and the Task-tool opt-in into settings.json.

Both exist for the same reason: Claude Code's MCP servers and plugin hooks
inherit the environment of the process that launched `claude`, not the user's
interactive shell. A prerequisite that is installed, exported and verified can
still be invisible to them, and restarting `claude` in a shell older than the
export changes nothing. Carrying the values in settings.json removes the
dependency on the shell entirely.

Scope note: the *properties* of the composed PATH — ordering, the
/usr/bin:/bin floor, dedupe, no working-directory injection — are covered in
tests/test_kit_compute_path.py, which drives the shell function directly with
controlled PATHs. They cannot be tested honestly from here: this harness puts
every stub in one directory that is already on PATH, so an implementation
that returned $PATH untouched would satisfy any assertion made at this level.
What belongs here is that install.sh writes the keys at all, and respects
values the user already set.
"""
import json

import pytest

from tests.helpers import run_install


@pytest.fixture(scope="module")
def installed():
    """One default install shared across the read-only assertions below.

    Each install.sh run costs ~4.5s, and five of these tests took identical
    arguments and produced byte-identical HOMEs — 41s to assert six things
    about one install.
    """
    return run_install()


def _settings(home):
    return json.loads((home / ".claude" / "settings.json").read_text())


def test_install_writes_env_path(installed):
    assert installed.returncode == 0, installed.stderr
    env = _settings(installed.home).get("env", {})
    assert "PATH" in env, (
        "settings.json env must carry a PATH; hooks and MCP servers inherit "
        "Claude Code's environment, not the login shell's"
    )


def test_persisted_path_covers_every_directory_the_install_ran_with(installed):
    """The property that makes this worth persisting: nothing the install
    could reach is missing from what gets written.

    This can fail — dropping or filtering inherited entries breaks it — where
    asserting that one known-present directory appears cannot, since that
    directory is on the inherited PATH already.
    """
    persisted = set(_settings(installed.home)["env"]["PATH"].split(":"))
    inherited = {p for p in f"{installed.fake_bin}:/usr/bin:/bin".split(":") if p}
    missing = inherited - persisted
    assert not missing, f"install-time PATH entries dropped: {sorted(missing)}"


def test_install_enables_the_task_tools(installed):
    """rule 40's Pre-Dispatch Protocol is built on TaskCreate/TaskUpdate/
    TaskList/TaskGet, which are opt-in on current model families. Without
    this key the kit mandates a protocol that cannot run."""
    env = _settings(installed.home).get("env", {})
    assert env.get("CLAUDE_CODE_ENABLE_TODO_TOOLS") == "1"


def test_user_env_wins_over_the_kit_default():
    """merge-policy gives env winner_on_conflict: user. A user who has set
    their own PATH keeps it, however wrong the kit thinks it is."""
    mine = "/only/mine"
    r = run_install(preexisting_settings=json.dumps({"env": {"PATH": mine}}))
    assert _settings(r.home)["env"]["PATH"] == mine


def test_user_opt_out_of_the_task_tools_is_respected():
    """Same rule, the other key. Someone who has deliberately disabled the
    Task tools must not have them switched back on by an install."""
    r = run_install(
        preexisting_settings=json.dumps(
            {"env": {"CLAUDE_CODE_ENABLE_TODO_TOOLS": "0"}}
        )
    )
    assert _settings(r.home)["env"]["CLAUDE_CODE_ENABLE_TODO_TOOLS"] == "0"
