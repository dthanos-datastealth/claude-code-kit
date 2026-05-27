#!/usr/bin/env python3
"""Enforce the 5-section schema on docs/tools/*.md files.

Required structure:
  # <name> — <one-line summary>
  **What it does:** ...
  **Why it's in this kit:** ...
  **When you'd disable it:** ...
  **Source:** ...
  **Cost / footprint:** ...

Usage: lint-tools-docs.py <file>... | lint-tools-docs.py -
Exit 0 if all docs valid, 1 otherwise.
"""
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "What it does:",
    "Why it's in this kit:",
    "When you'd disable it:",
    "Source:",
    "Cost / footprint:",
]
TITLE_RE = re.compile(r"^# \S.* — \S.*$", re.MULTILINE)


def check(name: str, text: str) -> list[str]:
    errs = []
    if not TITLE_RE.search(text):
        errs.append(f"{name}: missing or malformed title (expected '# <name> — <summary>')")
    for section in REQUIRED_SECTIONS:
        if f"**{section}**" not in text:
            errs.append(f"{name}: missing required section header '**{section}**'")
    return errs


def main() -> int:
    args = sys.argv[1:] or ["-"]
    all_errs: list[str] = []
    for arg in args:
        if arg == "-":
            all_errs += check("<stdin>", sys.stdin.read())
        else:
            p = Path(arg)
            all_errs += check(str(p), p.read_text())
    if all_errs:
        for e in all_errs:
            print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
