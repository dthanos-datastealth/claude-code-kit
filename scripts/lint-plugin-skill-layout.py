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


def declared_skill_dirs(plugin_root: Path) -> set[Path]:
    """Skill directories named by `plugin.json`'s `skills` field.

    Each entry names a directory that itself contains SKILL.md, so its SKILL.md
    is discoverable and must not be reported as a flat file.
    """
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return set()
    try:
        declared = json.loads(manifest.read_text()).get("skills")
    except (json.JSONDecodeError, OSError):
        return set()
    if isinstance(declared, str):
        declared = [declared]
    if not isinstance(declared, list):
        return set()
    return {(plugin_root / str(entry)).resolve() for entry in declared}


def undiscoverable_skills(plugin_root: Path) -> list[Path]:
    """Flat `*.md` files directly under the plugin's own top-level `skills/`."""
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return []
    exempt = declared_skill_dirs(plugin_root)
    findings = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            # A declared skill directory's own SKILL.md is discoverable.
            if entry.parent.resolve() in exempt:
                continue
            findings.append(entry)
    return findings


def scan(plugin_root: Path, label: str, errors: list[str]) -> None:
    if is_pruned(plugin_root, plugin_root.parent):
        return
    for flat in undiscoverable_skills(plugin_root):
        errors.append(
            f"{label}: skills/{flat.name} is a flat file — Claude Code discovers "
            f"skills only at skills/<name>/SKILL.md, so this never loads. Move it "
            f"to skills/{flat.stem}/SKILL.md (or to commands/ if it is a command)."
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
    for root, label in roots:
        scan(root, label, errors)

    if errors:
        print("\nUndiscoverable plugin skills found:", file=sys.stderr)
        for e in errors:
            print(f"  ✘ {e}", file=sys.stderr)
        return 1
    print("\nOK: every plugin skill is at a discoverable skills/<name>/SKILL.md path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
