"""Tests for plugins/claude-code-kit/scripts/fix-notion-mcp-port.sh."""
from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "plugins" / "claude-code-kit" / "scripts" / "fix-notion-mcp-port.sh"


def _write_fake_claude_cli(bin_dir: Path, log: Path) -> Path:
    """Fake `claude` CLI that logs all invocations to `log`."""
    fake = bin_dir / "claude"
    fake.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> "{log}"
        exit 0
    """))
    fake.chmod(0o755)
    return fake


def _run(*, port_arg: str | None = None, env_port: str | None = None,
         omit_claude: bool = False) -> tuple[subprocess.CompletedProcess, Path]:
    """Run script in an isolated env; return (proc, claude_log_path)."""
    with tempfile.TemporaryDirectory(prefix="fix-notion-test-") as td:
        td_p = Path(td)
        bin_dir = td_p / "bin"
        bin_dir.mkdir()
        log = td_p / "claude.log"
        log.touch()
        if not omit_claude:
            _write_fake_claude_cli(bin_dir, log)
        env = {
            "HOME": str(td_p),
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "LANG": "C.UTF-8",
        }
        if env_port:
            env["CLAUDE_NOTION_PORT"] = env_port
        args = ["bash", str(SCRIPT)]
        if port_arg:
            args.append(port_arg)
        proc = subprocess.run(args, env=env, text=True, capture_output=True)
        log_text = log.read_text() if log.exists() else ""
        return proc, log_text


def test_default_port_51234():
    proc, log = _run()
    assert proc.returncode == 0, f"script failed: {proc.stderr}"
    # Assert the parts that carry meaning, not the flag order — pinning the
    # whole string made adding --scope user look like a regression.
    add = next((ln for ln in log.splitlines() if ln.startswith("mcp add")), None)
    assert add is not None, f"expected an mcp add; log was:\n{log}"
    for fragment in ("--transport http", "--callback-port 51234", "notion",
                     "https://mcp.notion.com/mcp"):
        assert fragment in add, f"{fragment!r} missing from: {add}"
    # Must print the admin allow-list URL with the right port
    assert "http://localhost:51234/callback" in proc.stdout
    # Must mention Issue #55067 caveat
    assert "55067" in proc.stdout


def test_positional_port_overrides_default():
    proc, log = _run(port_arg="8080")
    assert proc.returncode == 0
    assert "callback-port 8080 notion" in log
    assert "http://localhost:8080/callback" in proc.stdout


def test_env_var_port_overrides_default():
    proc, log = _run(env_port="9090")
    assert proc.returncode == 0
    assert "callback-port 9090 notion" in log
    assert "http://localhost:9090/callback" in proc.stdout


def test_positional_overrides_env_var():
    """Positional arg wins over env var."""
    proc, log = _run(port_arg="7070", env_port="9090")
    assert proc.returncode == 0
    assert "callback-port 7070 notion" in log


def test_rejects_invalid_port_too_low():
    proc, _ = _run(port_arg="80")
    assert proc.returncode != 0
    assert "invalid port" in proc.stderr.lower()


def test_rejects_invalid_port_non_numeric():
    proc, _ = _run(port_arg="abc")
    assert proc.returncode != 0
    assert "invalid port" in proc.stderr.lower()


def test_aborts_when_claude_cli_missing():
    proc, _ = _run(omit_claude=True)
    assert proc.returncode != 0
    assert "claude cli" in proc.stderr.lower() or "claude" in proc.stderr.lower()


def test_registers_at_user_scope():
    """Without --scope user, `claude mcp add` writes to the CURRENT PROJECT's
    section of ~/.claude.json, not the user's. Observed:

        Added HTTP MCP server notion ... to local config
        File modified: ~/.claude.json [project: /Users/bob/claude-code-kit]

    The pinned port then applies only in the directory the script was run
    from. Everywhere else Notion goes back to a random callback port, which
    is the exact failure this script exists to fix — and the user gets no
    signal, because it works in the directory they tested from.
    """
    proc, log = _run()
    assert proc.returncode == 0
    # Assert on the ADD line specifically. `"--scope user" in log` is
    # satisfied by the three remove lines, which also carry the flag — so it
    # passed with the add left at its default local scope. Found by
    # scripts/mutate.py (mutant notion-port-defaults-to-local-scope).
    add = next((ln for ln in log.splitlines() if ln.startswith("mcp add")), None)
    assert add is not None, f"expected an mcp add; log was:\n{log}"
    assert "--scope user" in add, (
        f"the registration itself must be user-scoped, not project-scoped: {add}"
    )


def test_remove_clears_every_scope_not_just_the_one_being_written():
    """Precedence is local > project > user.

    `claude mcp add` defaults to LOCAL scope, so every earlier version of
    this script left a local-scoped `notion` behind. Removing only at user
    scope leaves that entry in place, and because local outranks user it
    silently wins over the pin this script just wrote — in the one directory
    the user originally ran it from, which is the directory they will test
    in. The documented verification reads only top-level `mcpServers`, so it
    reports success while the shadowing entry is the one in force.
    """
    proc, log = _run()
    assert proc.returncode == 0
    removed_scopes = {
        scope for scope in ("local", "project", "user")
        for ln in log.splitlines()
        if "mcp remove" in ln and f"--scope {scope}" in ln and "notion" in ln
    }
    assert removed_scopes == {"local", "project", "user"}, (
        "every scope must be cleared before the add, or a higher-precedence "
        f"leftover shadows it; cleared only {sorted(removed_scopes)}"
    )


def test_idempotent_remove_then_add():
    """Script does `claude mcp remove notion` (allowed to fail) then `add`."""
    proc, log = _run()
    assert proc.returncode == 0
    # Both remove and add must have been invoked, in that order, and the
    # remove must actually name notion — asserting the two words appear
    # somewhere in the log is satisfied by the add line alone.
    assert any("mcp remove" in ln and "notion" in ln for ln in log.splitlines())
    assert "mcp add" in log
    assert log.index("mcp remove") < log.index("mcp add")
    # And only writes to ~/.claude.json (via claude CLI) — no other side effects.
