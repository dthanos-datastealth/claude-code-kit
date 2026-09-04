#!/usr/bin/env python3
"""Shared plugin-cache traversal for the lints that scan installed plugins.

`lint-mcp-hardcoded-paths.py` and `lint-plugin-skill-layout.py` both need to
resolve a Claude home and walk `plugins/cache/<marketplace>/<plugin>/<version>`.
Each keeps its own glob, "nothing to scan" message and exit handling; only the
resolution and the version-directory enumeration live here (same reason
`_atomic.py` exists).
"""
from __future__ import annotations

from pathlib import Path

# Directories that never contain a plugin's own components. `node_modules` is
# the load-bearing one: a vendored dependency can ship its own `skills/` tree
# (chrome-devtools-mcp vendors one with flat .md files), and a depth-agnostic
# walk would report it as the plugin's.
PRUNED_DIR_NAMES = {"node_modules", ".git"}


def resolve_cache_root(argv_value: str | None = None) -> Path:
    """Return the `plugins/cache` directory for a Claude home."""
    return (Path(argv_value or "~/.claude").expanduser() / "plugins" / "cache").resolve()


def iter_plugin_versions(cache_root: Path):
    """Yieldevery `cache/<marketplace>/<plugin>/<version>` directory, sorted.

    A version directory is the plugin root: the thing that holds
    `.claude-plugin/`, `skills/`, `commands/`, `.mcp.json`.
    """
    if not cache_root.is_dir():
        return
    for marketplace in sorted(p for p in cache_root.iterdir() if p.is_dir()):
        for plugin in sorted(p for p in marketplace.iterdir() if p.is_dir()):
            for version in sorted(p for p in plugin.iterdir() if p.is_dir()):
                yield version


def is_pruned(path: Path, root: Path) -> bool:
    """True if `path` sits under a directory a plugin scan must not descend."""
    rel_parts = path.relative_to(root).parts if path != root else ()
    return any(
        part in PRUNED_DIR_NAMES or (part.startswith(".") and part != ".claude-plugin")
        for part in rel_parts
    )
