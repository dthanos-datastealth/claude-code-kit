#!/usr/bin/env python3
"""Fail if scrubbing-target patterns appear in the repository.

This is a public repository. Anything naming the author, their employer, their
customers, their machine or their filesystem is a disclosure, and the ones that
matter arrive as incidental detail — an absolute path in an example, a customer
name in a log string, a real defect recounted in a changelog entry.

Usage:
  lint-scrubbing.py              scan every tracked file (what CI runs)
  lint-scrubbing.py <file>...    scan specific files
  lint-scrubbing.py -            scan stdin

Exit 0 if clean, 1 if any pattern matched.

Note that with no arguments this used to read stdin, so running it bare scanned
nothing and reported success. It now scans the whole repository, which is the
only scope that makes it a gate.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Files that must contain the patterns in order to detect or test for them.
SELF_REFERENTIAL = {
    "scripts/lint-scrubbing.py",
    "tests/test_lint_scrubbing.py",
}

# A copyright line names its holder on purpose. That is the one place an
# organisation's name is a statement of ownership rather than a leak, and
# removing it would misstate who owns the work. Every other appearance is
# incidental and is what this lint exists to catch.
DELIBERATE = {"LICENSE"}

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


def tracked_files() -> list[Path]:
    """Every tracked text file, minus the two that must name the patterns."""
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"],
                         capture_output=True, text=True, check=True).stdout.split()
    skip = SELF_REFERENTIAL | DELIBERATE
    return [REPO / f for f in out if f not in skip]


def main() -> int:
    args = sys.argv[1:]
    all_hits: list[str] = []
    if args == ["-"]:
        all_hits += scan("<stdin>", sys.stdin.read())
    elif args:
        for arg in args:
            p = Path(arg)
            all_hits += scan(str(p), p.read_text())
    else:
        for p in tracked_files():
            try:
                text = p.read_text()
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable; nothing to scrub
            all_hits += scan(str(p.relative_to(REPO)), text)
    if all_hits:
        for h in all_hits:
            print(h, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
