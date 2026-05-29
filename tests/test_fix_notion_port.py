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
    # Must invoke `claude mcp add --transport http --callback-port 51234 notion ...`
    assert "mcp add --transport http --callback-port 51234 notion https://mcp.notion.com/mcp" in log, \
        f"expected mcp add with port 51234; log was:\n{log}"
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


def test_idempotent_remove_then_add():
    """Script does `claude mcp remove notion` (allowed to fail) then `add`."""
    proc, log = _run()
    assert proc.returncode == 0
    # Both remove and add must have been invoked
    assert "mcp remove notion" in log
    assert "mcp add" in log
    # And only writes to ~/.claude.json (via claude CLI) — no other side effects.
