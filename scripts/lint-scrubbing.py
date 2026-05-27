#!/usr/bin/env python3
"""Fail if scrubbing-target patterns appear in input.

Usage: lint-scrubbing.py <file>... | lint-scrubbing.py -
Exit 0 if clean, 1 if any pattern matched.
"""
import re
import sys
from pathlib import Path

PATTERNS = [
    r"/Users/dthanos\b",
    r"@psyigroup\.com\b",
    r"\bPSYI\b",
    r"\bWebStealth\b",
    r"\bDataStealth\b",
    r"\bManulife\b",
    r"\bNexus\b",
]


def scan(name: str, text: str) -> list[str]:
    hits = []
    for pat in PATTERNS:
        for m in re.finditer(pat, text):
            line_no = text.count("\n", 0, m.start()) + 1
            hits.append(f"{name}:{line_no}: matched /{pat}/ -> {m.group(0)!r}")
    return hits


def main() -> int:
    args = sys.argv[1:] or ["-"]
    all_hits: list[str] = []
    for arg in args:
        if arg == "-":
            all_hits += scan("<stdin>", sys.stdin.read())
        else:
            p = Path(arg)
            all_hits += scan(str(p), p.read_text())
    if all_hits:
        for h in all_hits:
            print(h, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
