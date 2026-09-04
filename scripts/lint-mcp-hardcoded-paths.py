#!/usr/bin/env python3
"""Scan every installed plugin's `.mcp.json` for owner-specific hardcoded paths.

This catches the failure mode where a plugin's `.mcp.json` references an
absolute path like `/Users/<owner>/...` or `/home/<owner>/...` that exists
only on the plugin author's machine. When such a plugin ships to other
users (or runs in an isolated HOME), the MCP server can't find the
referenced file and the plugin shows up as `✘ failed` in `claude mcp list`.

The kit hit this with an older version of one plugin's `.mcp.json`
that hardcoded `/Users/<owner>/.claude/certs/corporate-ca-bundle.pem`.
The upstream fork was fixed but the local cache stayed dirty; this
lint would have surfaced the bug the moment a plugin landed with
such a path.

The `command` field is judged more strictly than `env` values, because the
two fail differently. An `env` value like `/opt/homebrew/...` is portable
across users on one OS, which is all an env var has to be. A `command` is the
interpreter Claude Code executes: an absolute one is unportable across
*platforms*, so a plugin pinning `/opt/homebrew/bin/uvx` cannot start on Linux
at all. That is a real shipped failure the owner-path patterns below cannot
see, since `/opt/homebrew` names no user.

Usage:
  lint-mcp-hardcoded-paths.py <claude-home>
  lint-mcp-hardcoded-paths.py ~/.claude   # default if no arg

Exit 0 if no hardcoded owner paths found, 1 otherwise.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _plugin_cache import resolve_cache_root  # noqa: E402

# Patterns that indicate an owner-specific absolute path. We deliberately
# allow `/opt/homebrew/...`, `/usr/local/...`, `/etc/...`, etc. — those are
# system-wide and portable across users on the same OS.
SUSPICIOUS_PATTERNS = [
    (re.compile(r"/Users/[^/\s\"']+"), "macOS user home"),
    (re.compile(r"/home/[^/\s\"']+"), "Linux user home"),
    (re.compile(r"/var/folders/[^/\s\"']+"), "macOS per-user temp"),
    # Windows paths in JSON files are double-escaped: literal `C:\Users\bob`
    # appears on disk as the bytes `C:\\Users\\bob`. The raw-string form
    # below matches FOUR backslashes (two escaped pairs) followed by `Users`
    # then another escaped pair and the user name.
    (re.compile(r"C:\\\\Users\\\\[^/\\\s\"']+"), "Windows user home (JSON-encoded)"),
    # And the unencoded form too, in case a .mcp.json ever ships a Windows
    # path that wasn't JSON-escaped (e.g. authored in a tool that didn't escape).
    (re.compile(r"C:\\Users\\[^/\\\s\"']+"), "Windows user home (raw)"),
]

# Allow-list: substrings that, if matched, indicate a legitimate use
# (e.g. example paths in docs, ${HOME} env var templates).
ALLOWED_SUBSTRINGS = [
    "${HOME}",
    "$HOME",
    "${CLAUDE_PLUGIN_ROOT}",
    "/Users/example",
    "/Users/<owner>",
    "/home/alice",  # an example in docs/memory-system.md
]


def scan_text(text: str) -> list[tuple[str, str]]:
    """Return [(matched-substring, why-it's-suspicious)] for any hardcoded paths."""
    findings: list[tuple[str, str]] = []
    for pattern, why in SUSPICIOUS_PATTERNS:
        for m in pattern.finditer(text):
            match = m.group(0)
            if any(allowed in match for allowed in ALLOWED_SUBSTRINGS):
                continue
            findings.append((match, why))
    return findings


# A plugin's `command` must resolve through PATH or through a variable Claude
# Code expands per machine. Anything else pins one platform's filesystem.
ALLOWED_COMMAND_PREFIXES = ("${CLAUDE_PLUGIN_ROOT}", "${HOME}", "$HOME")


def scan_commands(payload: dict) -> list[tuple[str, str]]:
    """Return [(server, command)] for each non-portable `command` value."""
    findings: list[tuple[str, str]] = []
    servers = payload.get("mcpServers")
    if not isinstance(servers, dict):
        return findings
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        command = spec.get("command")
        if not isinstance(command, str) or "/" not in command:
            continue
        if command.startswith(ALLOWED_COMMAND_PREFIXES):
            continue
        findings.append((str(name), command))
    return findings


def main() -> int:
    plugins_cache = resolve_cache_root(sys.argv[1] if len(sys.argv) > 1 else None)
    if not plugins_cache.exists():
        print(f"OK: no plugin cache at {plugins_cache} (nothing to scan)")
        return 0

    mcp_files = sorted(plugins_cache.rglob(".mcp.json"))
    if not mcp_files:
        print(f"OK: no .mcp.json files found in {plugins_cache}/")
        return 0
    print(f"Scanning {len(mcp_files)} .mcp.json files under {plugins_cache}/...")

    errors: list[str] = []
    for mcp in mcp_files:
        try:
            text = mcp.read_text()
        except Exception as e:
            errors.append(f"{mcp}: could not read ({e})")
            continue
        # Sanity-check: the file should parse as JSON
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            errors.append(f"{mcp}: invalid JSON ({e})")
            continue
        findings = scan_text(text)
        if findings:
            for match, why in findings:
                rel = mcp.relative_to(plugins_cache)
                errors.append(f"{rel}: {why!r} hardcoded path: {match!r}")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {}
        for server, command in scan_commands(payload):
            rel = mcp.relative_to(plugins_cache)
            errors.append(
                f"{rel}: mcpServers.{server}.command is an absolute path "
                f"({command!r}); it cannot resolve on another platform. Use a "
                f"bare executable name resolved from PATH, or a "
                f"${{CLAUDE_PLUGIN_ROOT}}-relative path."
            )

    if errors:
        print("\nHardcoded owner-specific paths found:", file=sys.stderr)
        for e in errors:
            print(f"  ✘ {e}", file=sys.stderr)
        print(
            "\nThese paths only exist on the plugin author's machine. "
            "The plugin will fail to load on other users' machines or in "
            "isolated HOMEs. Fix by replacing with an env var (e.g. "
            "${HOME}/.config/...) or removing the env entry entirely "
            "and documenting how users supply it themselves.",
            file=sys.stderr,
        )
        return 1
    print("\nOK: no hardcoded owner-specific paths found in any plugin's .mcp.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
