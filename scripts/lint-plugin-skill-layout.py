#!/usr/bin/env python3
"""Flag plugin skills that Claude Code cannot discover.

Claude Code discovers a plugin's skills at `skills/<name>/SKILL.md` — one
directory per skill. A flat `skills/<name>.md` is not a discovery path, so the
file is silently invisible: no error, no warning, the skill simply never
appears. Flat markdown belongs in `commands/`.

This is the check that would have caught a shipped plugin whose six skills had
never loaded on any install.

Resolving a plugin's skills root needs three rules, and all three matter:

1. The root is the plugin directory's own top-level `skills/`. A `skills` entry
   in `plugin.json` names an additional *skill directory* (it holds a SKILL.md),
   not another root — reading it as a root would flag the SKILL.md inside it as
   a flat file.
2. Prune `node_modules/`, `.git/` and dot-directories. A vendored dependency can
   ship its own `skills/` tree, which is not the plugin's.
3. An intermediate namespace level (`skills/<ns>/<name>/SKILL.md`) is a
   container, not a skill.

Usage:
  lint-plugin-skill-layout.py                     # scan the installed plugin cache
  lint-plugin-skill-layout.py <claude-home>       # scan a specific Claude home
  lint-plugin-skill-layout.py <plugin-dir> ...    # scan plugin directories directly

Exit 0 if every skill is discoverable, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _plugin_cache import is_pruned, iter_plugin_versions, resolve_cache_root  # noqa: E402


def has_frontmatter(path: Path) -> bool:
    """True if the file opens with a YAML frontmatter block.

    This does NOT decide whether a file is a skill — the docs are explicit that
    every frontmatter field is optional (skills.md:330 "All fields are
    optional"; `name` defaults to the directory name at :338; `description`
    falls back to the first paragraph at :339), so a skill loads without any.

    It decides only how confident the report can be. A flat `.md` carrying
    frontmatter is a skill at a path that cannot load, and is reported as an
    error. One without it may be a skill or may be a build fragment sharing the
    directory — `caveman` keeps `native-core.md` beside `compile.mjs` and
    `generated/` — so it is reported as a warning for a human to judge, rather
    than failing the gate on another project's layout.
    """
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.strip() == "":
                    continue  # tolerate leading blank lines
                return line.rstrip("\r\n").strip() == "---"
    except OSError:
        return False
    return False


def undiscoverable_skills(plugin_root: Path) -> tuple[list[Path], list[Path]]:
    """Flat `*.md` files directly under the plugin's own top-level `skills/`.

    Returns (certain, possible): those carrying frontmatter, and those not.
    """
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return [], []
    # Only files directly under skills/ are candidates, and a manifest `skills`
    # entry names a directory one level below that — so a declared skill's own
    # SKILL.md is never in this loop and needs no exemption. An exemption check
    # used to sit here; it could not fire for that stated purpose, and the one
    # case it did fire for defeated the lint, since a plugin declaring
    # `skills: ["skills"]` matched the root and suppressed all its own findings.
    certain: list[Path] = []
    possible: list[Path] = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            (certain if has_frontmatter(entry) else possible).append(entry)
    return certain, possible


def scan(plugin_root: Path, label: str, errors: list[str],
         warnings: list[str]) -> None:
    if is_pruned(plugin_root, plugin_root.parent):
        return
    certain, possible = undiscoverable_skills(plugin_root)
    for flat in certain:
        errors.append(
            f"{label}: skills/{flat.name} is a flat file — Claude Code discovers "
            f"skills only at skills/<name>/SKILL.md, so this never loads. Move it "
            f"to skills/{flat.stem}/SKILL.md (or to commands/ if it is a command)."
        )
    for flat in possible:
        warnings.append(
            f"{label}: skills/{flat.name} is a flat file with no frontmatter. If "
            f"it is a skill it never loads and belongs at skills/{flat.stem}/"
            f"SKILL.md; if it is a build input or a fragment, it is fine where it is."
        )


def main() -> int:
    args = sys.argv[1:]
    roots: list[tuple[Path, str]] = []

    plugin_dirs = [Path(a) for a in args if (Path(a) / ".claude-plugin").is_dir()]
    if plugin_dirs:
        roots = [(p.resolve(), str(p)) for p in plugin_dirs]
        print(f"Scanning {len(roots)} plugin directories...", flush=True)
    else:
        cache_root = resolve_cache_root(args[0] if args else None)
        versions = list(iter_plugin_versions(cache_root))
        if not versions:
            print(f"OK: no installed plugins under {cache_root}/ (nothing to scan)")
            return 0
        roots = [(v, str(v.relative_to(cache_root))) for v in versions]
        print(f"Scanning {len(roots)} installed plugin versions under {cache_root}/...", flush=True)

    errors: list[str] = []
    warnings: list[str] = []
    for root, label in roots:
        scan(root, label, errors, warnings)

    if warnings:
        print("\nFlat markdown under skills/, no frontmatter — check these by hand:",
              file=sys.stderr)
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)

    if errors:
        print("\nUndiscoverable plugin skills found:", file=sys.stderr)
        for e in errors:
            print(f"  ✘ {e}", file=sys.stderr)
        return 1
    print("\nOK: every plugin skill is at a discoverable skills/<name>/SKILL.md path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
