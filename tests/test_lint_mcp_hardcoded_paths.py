"""Tests for scripts/lint-mcp-hardcoded-paths.py.

Covers the command-field rule specifically: an absolute `command` is
unportable across platforms even when it names no user, which is how a
plugin pinning /opt/homebrew/bin/uvx shipped and could not start on Linux.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lint-mcp-hardcoded-paths.py"


def _cache(tmp_path: Path, manifest: dict) -> Path:
    home = tmp_path / "home" / ".claude"
    d = home / "plugins" / "cache" / "mkt" / "plug" / "1.0.0"
    d.mkdir(parents=True)
    (d / ".mcp.json").write_text(json.dumps(manifest))
    return home


def _run(home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(home)], text=True, capture_output=True
    )


def test_absolute_homebrew_command_is_flagged(tmp_path):
    home = _cache(tmp_path, {"mcpServers": {"berry": {"command": "/opt/homebrew/bin/uvx"}}})
    r = _run(home)
    assert r.returncode == 1
    assert "command" in r.stderr and "/opt/homebrew/bin/uvx" in r.stderr


def test_bare_command_passes(tmp_path):
    home = _cache(tmp_path, {"mcpServers": {"berry": {"command": "uvx", "args": ["x"]}}})
    r = _run(home)
    assert r.returncode == 0, r.stderr


def test_plugin_root_relative_command_passes(tmp_path):
    home = _cache(
        tmp_path,
        {"mcpServers": {"s": {"command": "${CLAUDE_PLUGIN_ROOT}/scripts/server"}}},
    )
    r = _run(home)
    assert r.returncode == 0, r.stderr


def test_homebrew_in_an_env_value_still_passes(tmp_path):
    """env values are judged by portability across users, not platforms — this
    behaviour is deliberately unchanged by the command-field rule."""
    home = _cache(
        tmp_path,
        {"mcpServers": {"s": {"command": "uvx", "env": {"CA": "/opt/homebrew/etc/ca.pem"}}}},
    )
    r = _run(home)
    assert r.returncode == 0, r.stderr


def test_owner_path_in_env_is_still_flagged(tmp_path):
    home = _cache(
        tmp_path,
        {"mcpServers": {"s": {"command": "uvx", "env": {"CA": "/Users/someone/ca.pem"}}}},
    )
    r = _run(home)
    assert r.returncode == 1
    assert "/Users/someone" in r.stderr
