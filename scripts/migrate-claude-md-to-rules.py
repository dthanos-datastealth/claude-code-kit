#!/usr/bin/env python3
"""Move the kit's sections out of a user's CLAUDE.md, once.

The kit used to merge its instructions into `~/.claude/CLAUDE.md`, section by
section, against a hand-maintained manifest. It now ships them as files under
`~/.claude/rules/`, which Claude Code discovers rather than merges. This script
is the bridge: it removes the sections the kit owned so the user is not left
running two copies of every rule, and leaves everything else exactly as it was.

It is the last use of the manifest and of the merger's section parser. Once a
machine has been migrated, the kit never writes that file again.

Usage:
  migrate-claude-md-to-rules.py <claude-md> [--manifest P] [--dry-run]

Exit codes:
  0  migrated (or, with --dry-run, would have)
  2  bad arguments or unreadable input
  3  nothing to do: no kit-owned section present
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO / "claude" / "CLAUDE.md.manifest.json"

STAMP = (
    "<!-- The kit's instructions used to live in this file. They now ship as\n"
    "     owned files under ~/.claude/rules/, which Claude Code loads every\n"
    "     session. This file is yours again: the kit does not write it.\n"
    "     To override a kit rule, use ~/.claude/rules/00-user-overrides.md. -->"
)


def _load_merger():
    """Import the merger by path — its filename has hyphens, so it is not a
    module name Python can import directly."""
    spec = importlib.util.spec_from_file_location(
        "kit_merger", REPO / "scripts" / "intelligent-claude-md-merge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kit_owned_sections(text: str, manifest: dict) -> list[str]:
    """Heading lines in `text` that the manifest says the kit owns."""
    merger = _load_merger()
    owned = manifest.get("owned_sections", [])
    return [
        s["heading_line"]
        for s in merger.parse_sections(text)
        if s["heading_line"]
        and merger.matches_owned(s["heading_line"], s["depth"], owned) is not None
    ]


def strip_kit_sections(text: str, manifest: dict) -> tuple[str, list[str]]:
    """Return (text without kit-owned sections, the headings removed)."""
    merger = _load_merger()
    owned = manifest.get("owned_sections", [])

    kept, removed = [], []
    for section in merger.parse_sections(text):
        h = section["heading_line"]
        if h and merger.matches_owned(h, section["depth"], owned) is not None:
            removed.append(h)
            continue
        kept.append(section)

    return merger.serialize_sections(kept), removed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claude_md", type=Path)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be removed; write nothing")
    args = ap.parse_args(argv)

    if not args.claude_md.is_file():
        print(f"error: not a file: {args.claude_md}", file=sys.stderr)
        return 2
    if not args.manifest.is_file():
        print(f"error: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    original = args.claude_md.read_text()
    manifest = json.loads(args.manifest.read_text())

    merged, removed = strip_kit_sections(original, manifest)
    if not removed:
        print("nothing to migrate: no kit-owned section found")
        return 3

    for h in removed:
        print(f"  moved to ~/.claude/rules/: {h}")

    if args.dry_run:
        print("  (dry-run: CLAUDE.md not written)")
        return 0

    body = merged.strip("\n")
    args.claude_md.write_text(f"{STAMP}\n\n{body}\n" if body else f"{STAMP}\n")
    print(f"  {len(removed)} section(s) moved; the rest of CLAUDE.md is untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
