#!/usr/bin/env python3
"""Heading-based CLAUDE.md merger with 3-way conflict detection.

For each kit-owned section declared in CLAUDE.md.manifest.json, compare:
  - user (live ~/.claude/CLAUDE.md)
  - kit_previous (cached snapshot from the last install/upgrade)
  - kit_new (the version being installed)

Decision matrix per section:
  live == kit_prev               → take kit_new (clean upgrade)
  live == kit_new                → no-op
  live != kit_prev, kit_prev ==
      kit_new                    → keep live (user modified, kit didn't)
  live != all                    → CONFLICT — prompt user

Sections NOT in the manifest are preserved verbatim from user.

Modes:
  --mode apply        merge into user file (interactive conflict prompts)
  --mode dry-run      print proposed changes, don't write
  --mode status       list unresolved conflicts in --conflict-dir

Output: merged CLAUDE.md written atomically (tmpfile + os.replace).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Shared atomic-write helper (replaces previously-inline tmpfile+os.replace).
sys.path.insert(0, str(Path(__file__).parent))
from _atomic import atomic_write_text  # noqa: E402

DEFAULT_MANIFEST = Path(__file__).parent.parent / "claude" / "CLAUDE.md.manifest.json"


def parse_sections(text: str) -> list[dict]:
    """Parse CLAUDE.md into ordered list of sections.

    Each section: {"heading_line": str, "depth": int, "body": str}
    where body is the lines BELOW the heading up to the next heading
    of equal or higher precedence (lower depth number).

    The leading content before any heading is captured as a section
    with heading_line="" and depth=0.
    """
    lines = text.split("\n")
    sections: list[dict] = []
    current: dict | None = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            # New heading
            if current is not None:
                sections.append(current)
            current = {
                "heading_line": line,
                "depth": len(m.group(1)),
                "body_lines": [],
            }
        else:
            if current is None:
                # Pre-heading prelude
                current = {"heading_line": "", "depth": 0, "body_lines": []}
            current["body_lines"].append(line)
    if current is not None:
        sections.append(current)
    for s in sections:
        s["body"] = "\n".join(s["body_lines"])
        del s["body_lines"]
    return sections


def serialize_sections(sections: list[dict]) -> str:
    """Inverse of parse_sections; produces the merged CLAUDE.md text."""
    parts = []
    for s in sections:
        if s["heading_line"]:
            parts.append(s["heading_line"])
        if s["body"]:
            parts.append(s["body"])
    return "\n".join(parts) if parts else ""


def matches_owned(heading_line: str, depth: int, owned: list[dict]) -> dict | None:
    """Return the owned-section entry matching this heading, else None."""
    for entry in owned:
        if entry.get("depth") != depth:
            continue
        h = entry["heading"]
        match = entry.get("match", "exact")
        if match == "exact" and heading_line.strip() == h:
            return entry
        if match == "prefix" and heading_line.strip().startswith(h):
            return entry
    return None


def index_by_heading(sections: list[dict]) -> dict[str, dict]:
    """Map heading_line → section. Last occurrence wins on duplicates."""
    return {s["heading_line"]: s for s in sections if s["heading_line"]}


def decide(live: str, prev: str, new: str) -> str:
    """3-way decision. Returns 'take_new' | 'keep_live' | 'conflict' | 'noop'."""
    if live == prev:
        return "take_new" if new != live else "noop"
    if live == new:
        return "noop"
    if prev == new:
        return "keep_live"
    return "conflict"


def prompt_conflict(heading_line: str, live: str, prev: str, new: str,
                    conflict_dir: Path) -> str:
    """Interactive prompt. Returns 'take_new' | 'keep_live' | 'wrote_conflict' | 'abort'."""
    print(f"\nCONFLICT: section {heading_line!r}", flush=True)
    print("  Your version (live):    diverged from kit-previous + kit-new", flush=True)
    print("  Diff (kit-previous → live):", flush=True)
    for d in unified_diff(prev, live):
        print(f"    {d}", flush=True)
    print("  Diff (kit-previous → kit-new):", flush=True)
    for d in unified_diff(prev, new):
        print(f"    {d}", flush=True)
    print("  Choose: [k] take kit_new  [y] keep yours  [m] write conflict file + skip  [a] abort", flush=True)
    choice = sys.stdin.readline().strip().lower()
    if choice == "k":
        return "take_new"
    if choice == "y":
        return "keep_live"
    if choice == "m":
        conflict_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", heading_line).strip("-")[:40]
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        cf = conflict_dir / f"{ts}-CLAUDE.md-{slug}.conflict.md"
        cf.write_text(
            f"# Conflict for section: {heading_line}\n\n"
            "<<<<<<< yours (live)\n" + live + "\n"
            "======= kit_previous\n" + prev + "\n"
            "======= kit_new\n" + new + "\n"
            ">>>>>>> end\n"
        )
        return "wrote_conflict"
    return "abort"


def unified_diff(a: str, b: str) -> list[str]:
    """Minimal unified-diff-ish output for two strings (no third-party deps)."""
    import difflib
    return list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                       lineterm="", n=2))[:20]


def merge(live_text: str, prev_text: str, new_text: str, manifest: dict,
          conflict_dir: Path | None, interactive: bool) -> tuple[str, list[str], list[str]]:
    """Merge live + prev + new per manifest. Returns (merged_text, conflicts, abort_reason).
    If abort_reason non-empty, merged_text should NOT be written.
    """
    owned = manifest.get("owned_sections", [])
    live_sections = parse_sections(live_text)
    prev_sections = parse_sections(prev_text)
    new_sections = parse_sections(new_text)

    prev_by_heading = index_by_heading(prev_sections)
    new_by_heading = index_by_heading(new_sections)

    out: list[dict] = []
    handled_new = set()
    conflicts: list[str] = []
    aborts: list[str] = []

    for section in live_sections:
        h = section["heading_line"]
        d = section["depth"]
        owned_entry = matches_owned(h, d, owned) if h else None
        if not owned_entry:
            # User-owned section (or prelude) — preserve verbatim
            out.append(section)
            continue
        # Kit-owned section in live: 3-way decide
        live_body = section["body"]
        prev_body = prev_by_heading.get(h, {}).get("body", "")
        new_body = new_by_heading.get(h, {}).get("body", "")
        handled_new.add(h)
        decision = decide(live_body, prev_body, new_body)
        if decision == "take_new":
            new_section = new_by_heading.get(h, section)
            out.append({"heading_line": h, "depth": d, "body": new_section["body"]})
        elif decision in ("keep_live", "noop"):
            out.append(section)
        elif decision == "conflict":
            if not interactive:
                conflicts.append(h)
                out.append(section)  # leave live in place for non-interactive
                continue
            choice = prompt_conflict(h, live_body, prev_body, new_body,
                                      conflict_dir or Path("."))
            if choice == "take_new":
                out.append({"heading_line": h, "depth": d, "body": new_by_heading[h]["body"]})
            elif choice == "keep_live":
                out.append(section)
            elif choice == "wrote_conflict":
                conflicts.append(h)
                out.append(section)
            else:  # abort
                aborts.append(h)
                return "", conflicts, aborts

    # Sections in kit_new but not in live: append at end if kit-owned
    for new_section in new_sections:
        h = new_section["heading_line"]
        if not h or h in handled_new:
            continue
        owned_entry = matches_owned(h, new_section["depth"], owned)
        if owned_entry:
            out.append(new_section)

    return serialize_sections(out), conflicts, aborts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit_new", type=Path, help="Kit's current CLAUDE.md (the new version)")
    parser.add_argument("user", type=Path, help="User's live CLAUDE.md")
    parser.add_argument("--prev", type=Path, help="Cached kit_previous CLAUDE.md")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--conflict-dir", type=Path)
    parser.add_argument("--mode", choices=["apply", "dry-run", "status"], default="apply")
    args = parser.parse_args(argv)

    if args.mode == "status":
        cd = args.conflict_dir
        if cd is None or not cd.exists():
            print("(no conflict dir; nothing to report)")
            return 0
        files = sorted(cd.glob("*.conflict.md"))
        if not files:
            print("(no unresolved conflicts)")
            return 0
        for f in files:
            print(f.name)
        return 0

    if not args.kit_new.exists():
        print(f"error: kit CLAUDE.md not found: {args.kit_new}", file=sys.stderr)
        return 2
    if not args.user.exists():
        print(f"error: user CLAUDE.md not found: {args.user}", file=sys.stderr)
        return 2
    if not args.manifest.exists():
        print(f"error: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    # Block if unresolved conflicts pending
    if args.conflict_dir is not None and args.conflict_dir.exists():
        pending = sorted(args.conflict_dir.glob("*.conflict.md"))
        if pending and args.mode != "status":
            print(f"error: unresolved conflict files exist in {args.conflict_dir}",
                  file=sys.stderr)
            for f in pending:
                print(f"  {f.name}", file=sys.stderr)
            print("Resolve (delete) these files before running upgrade again.",
                  file=sys.stderr)
            return 3

    live_text = args.user.read_text()
    new_text = args.kit_new.read_text()
    prev_text = args.prev.read_text() if args.prev and args.prev.exists() else ""
    manifest = json.loads(args.manifest.read_text())

    merged, conflicts, aborts = merge(
        live_text, prev_text, new_text, manifest,
        conflict_dir=args.conflict_dir,
        interactive=(args.mode == "apply"),
    )

    if aborts:
        print(f"CONFLICT: aborted on section {aborts[0]!r}; no changes written.",
              file=sys.stderr)
        return 4

    if args.mode == "dry-run":
        # Print summary; don't write
        print("--- dry-run summary ---")
        if conflicts:
            print(f"  conflicts: {len(conflicts)} (would prompt or write to conflict dir)")
        if merged != live_text:
            print(f"  changed bytes: {abs(len(merged) - len(live_text))} delta")
        else:
            print("  no changes")
        return 0

    if merged:
        atomic_write_text(args.user, merged)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
