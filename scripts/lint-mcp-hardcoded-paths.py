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

# Patterns that indicate an owner-specific absolute path. We deliberately
# allow `/opt/homebrew/...`, `/usr/local/...`, `/etc/...`, etc. — those are
# system-wide and portable across users on the same OS.
SUSPICIOUS_PATTERNS = [
    (re.compile(r"/Users/[^/\s\"']+"), "macOS user home"),
    (re.compile(r"/home/[^/\s\"']+"), "Linux user home"),
    (re.compile(r"/var/folders/[^/\s\"']+"), "macOS per-user temp"),
    (re.compile(r"C:\\Users\\[^/\\\s\"']+"), "Windows user home"),
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


def main() -> int:
    claude_home = Path(sys.argv[1] if len(sys.argv) > 1 else "~/.claude").expanduser()
    plugins_cache = claude_home / "plugins" / "cache"
    if not plugins_cache.exists():
        print(f"OK: no plugin cache at {plugins_cache} (nothing to scan)")
        return 0

    mcp_files = sorted(plugins_cache.rglob(".mcp.json"))
    print(f"Scanning {len(mcp_files)} .mcp.json files under {plugins_cache}/...")
    if not mcp_files:
        print("OK: no .mcp.json files found in plugin cache")
        return 0

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
