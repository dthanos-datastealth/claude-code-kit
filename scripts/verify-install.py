#!/usr/bin/env python3
"""Assert that an install produced the artifacts it should have.

Called by scripts/test-install-isolated.sh against an isolated HOME, and
usable by hand against a real one.

This lives here rather than inline in the harness for one reason: the harness
asserted `CLAUDE.md` unconditionally, and install.sh stopped writing it at
Claude Code 2.0.64. Every run therefore failed at that assertion — four steps
before the leak check the harness exists to perform. A shell `for` loop over
filenames could not be tested; this can be, and is, in
tests/test_verify_install.py.

Which instruction artifact to expect depends on the CLI the install ran
against, so the caller states it rather than this script guessing:

  --expect-rules      >= 2.0.64: rules/ carries the kit's instructions and
                      CLAUDE.md belongs to the user
  --expect-claude-md  <  2.0.64: rules/ is ignored by the CLI, so the
                      CLAUDE.md template is the only thing that reaches Claude

Usage: verify-install.py <claude-home> (--expect-rules | --expect-claude-md)
Exit 0 if every expected artifact is present, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The kit rule files install.sh ships. 00-user-overrides.md is seeded once and
# is the user's thereafter, so it is expected to exist but never compared.
KIT_RULE_PREFIXES = ("10-", "20-", "30-", "40-", "50-", "60-")


def verify(home: Path, expect: str) -> list[str]:
    """Return a list of problems. Empty means the install is sound."""
    problems: list[str] = []

    def require_file(rel: str) -> None:
        if not (home / rel).is_file():
            problems.append(f"missing file: {rel}")

    def require_dir(rel: str) -> None:
        if not (home / rel).is_dir():
            problems.append(f"missing directory: {rel}")

    require_file("settings.json")
    require_file("memory/MEMORY.md")
    require_dir("docs/tools")

    if expect == "rules":
        rules = home / "rules"
        if not rules.is_dir():
            problems.append("missing directory: rules/")
        else:
            present = {p.name for p in rules.glob("*.md")}
            missing = [
                p for p in KIT_RULE_PREFIXES
                if not any(n.startswith(p) for n in present)
            ]
            if missing:
                problems.append(
                    "rules/: no file for prefix(es) " + ", ".join(missing)
                )
            if "00-user-overrides.md" not in present:
                problems.append("rules/: 00-user-overrides.md was not seeded")
        # Deliberately no CLAUDE.md assertion. Above the floor the kit does
        # not write it, and a user who has none is in the expected state.
    else:
        require_file("CLAUDE.md")

    settings = home / "settings.json"
    if settings.is_file():
        try:
            data = json.loads(settings.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"settings.json is not valid JSON: {exc}")
        else:
            if not data.get("enabledPlugins"):
                problems.append("settings.json: enabledPlugins is empty")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claude_home", type=Path)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--expect-rules", action="store_const",
                       dest="expect", const="rules")
    group.add_argument("--expect-claude-md", action="store_const",
                       dest="expect", const="claude-md")
    args = ap.parse_args()

    # Report every problem, not just the first. One stale assertion masking
    # the rest is how the leak check went unnoticed.
    problems = verify(args.claude_home, args.expect)
    if problems:
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    counts = []
    tools = args.claude_home / "docs" / "tools"
    counts.append(f"{len(list(tools.glob('*.md')))} per-tool docs")
    if args.expect == "rules":
        counts.append(f"{len(list((args.claude_home / 'rules').glob('*.md')))} rule files")
    plugins = json.loads((args.claude_home / "settings.json").read_text())
    counts.append(f"{len(plugins.get('enabledPlugins', {}))} plugins enabled")
    print("  " + "; ".join(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
