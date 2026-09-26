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


# A `**Source:**` section that exists but names nothing leaves a reader with no
# way to obtain the tool. That is how the dual-graph MCP — the FIRST step of
# CLAUDE.md's mandatory search order — shipped documented but unobtainable: the
# section was present, so the schema check passed, while its body said only to
# follow "the upstream project's" instructions. Require a locator: a URL or bare
# domain with a path, which is what every other Source section already carries.
LOCATOR_RE = re.compile(r"[\w-]+\.(?:com|org|io|dev|sh|ai)/\S")


def section_body(text: str, header: str, stops: "list[str] | None" = None) -> str:
    """Text between the `**<header>**` line and the next section header.

    With `stops`, only those headers end the section, so a bold sub-heading
    inside it (spec-kit's "**Hard prohibitions ...:**") stays part of the body.
    """
    marker = f"**{header}**"
    start = text.find(marker)
    if start == -1:
        return ""
    rest = text[start + len(marker) :]
    if stops is None:
        pattern = r"^\*\*[^*]+:\*\*"
    else:
        pattern = "^(?:" + "|".join(re.escape(f"**{s}**") for s in stops) + ")"
    nxt = re.search(pattern, rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def source_body(text: str) -> str:
    return section_body(text, "Source:")


def check(name: str, text: str) -> list[str]:
    errs = []
    if not TITLE_RE.search(text):
        errs.append(f"{name}: missing or malformed title (expected '# <name> — <summary>')")
    for section in REQUIRED_SECTIONS:
        if f"**{section}**" not in text:
            errs.append(f"{name}: missing required section header '**{section}**'")
    if f"**{REQUIRED_SECTIONS[3]}**" in text and not LOCATOR_RE.search(source_body(text)):
        errs.append(
            f"{name}: '**Source:**' names no locator — add the URL, repository or "
            f"package a reader can actually fetch the tool from"
        )
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
