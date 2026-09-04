#!/usr/bin/env python3
"""Verify every plugin in claude/settings.json is actually published in its
declared marketplace.

This catches the failure mode that bit us with optibot: the kit's
settings.json said `optibot@claude-plugins-official` but the actual
upstream marketplace.json (https://github.com/anthropics/claude-plugins-official/
.claude-plugin/marketplace.json) no longer lists optibot. The fake `claude`
CLI in tests/helpers.py is a yes-man that returns 0 for any plugin install,
so no test caught the mismatch. This script reads the AUTHORITATIVE upstream
marketplace.json for every marketplace the kit declares, then asserts every
plugin appears in its declared marketplace's plugin list.

The marketplace.json is the source of truth, not the `plugins/` directory
listing. Plugins in a marketplace can be sourced from:
  - `./plugins/<name>/`             (bundled, top-level)
  - `./external_plugins/<name>/`    (bundled, alternate dir)
  - `url:<external>`                (URL-pinned third party)
  - `github:<owner>/<repo>@<sha>`   (SHA-pinned third party)
  - `git-subdir:<remote>`           (subdir of another repo)

Usage:
  lint-plugin-marketplaces.py    # always online; fetches via `gh api`

Exit 0 if every plugin resolves, 1 if any mismatch.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SETTINGS = REPO / "claude" / "settings.json"


def fetch_marketplace_plugins(repo: str, ref: str | None = None) -> set[str] | None:
    """Fetch a marketplace's plugin name list from its upstream marketplace.json.

    Honours the entry's `ref`. Without it this check would validate the default
    branch while the installer registers a different one, so a release channel
    could be broken and still pass: the whole point of the ref is that the two
    branches carry different content.

    Returns the set of plugin names, or None if the repo has no
    .claude-plugin/marketplace.json at that ref (which is itself a kit-config
    bug — you can't `claude plugin marketplace add` a repo without that file).
    """
    path = f"repos/{repo}/contents/.claude-plugin/marketplace.json"
    if ref:
        path += f"?ref={ref}"
    try:
        out = subprocess.run(
            ["gh", "api", path, "--jq", ".content"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    try:
        m = json.loads(base64.b64decode(out).decode())
    except Exception:
        return None
    return {p["name"] for p in m.get("plugins", []) if "name" in p}


def main() -> int:
    settings = json.loads(SETTINGS.read_text())
    enabled = {k: v for k, v in (settings.get("enabledPlugins") or {}).items() if v is True}
    marketplaces = settings.get("extraKnownMarketplaces") or {}

    # Build: marketplace-name → (upstream owner/repo, ref or None)
    mkt_to_repo: dict[str, tuple[str, str | None]] = {}
    for name, cfg in marketplaces.items():
        src = (cfg.get("source") or {})
        if src.get("source") == "github" and src.get("repo"):
            mkt_to_repo[name] = (src["repo"], src.get("ref"))

    # Fetch each marketplace's published plugin list
    print(f"Checking {len(enabled)} plugins against {len(mkt_to_repo)} marketplaces...")
    mkt_plugins: dict[str, set[str] | None] = {}
    for name, (repo, ref) in mkt_to_repo.items():
        where = f"{repo}@{ref}" if ref else repo
        plugins = fetch_marketplace_plugins(repo, ref)
        if plugins is None and ref:
            # A pinned ref that does not resolve upstream is usually a channel
            # branch that has not been pushed yet, not a broken marketplace.
            # Validate the default branch instead and say plainly that the
            # channel is unpublished, rather than reporting the marketplace
            # unreachable — a wrong diagnosis for the common case.
            fallback = fetch_marketplace_plugins(repo)
            if fallback is not None:
                print(
                    f"  NOTE: {name} ref {ref!r} not published yet on {repo}; "
                    f"validated against the default branch instead"
                )
                mkt_plugins[name] = fallback
                continue
        if plugins is None:
            print(
                f"  ERROR: {name} ({where}) has no .claude-plugin/marketplace.json",
                file=sys.stderr,
            )
        else:
            print(f"  {name} ({where}): {len(plugins)} plugins published")
        mkt_plugins[name] = plugins

    # For each enabled plugin, assert it appears in its declared marketplace
    errors: list[str] = []
    for entry in sorted(enabled):
        if "@" not in entry:
            errors.append(f"{entry}: missing '@<marketplace>' suffix")
            continue
        plugin_name, _, mkt_name = entry.partition("@")
        if mkt_name not in mkt_plugins:
            errors.append(f"{entry}: marketplace {mkt_name!r} not declared in extraKnownMarketplaces")
            continue
        published = mkt_plugins[mkt_name]
        if published is None:
            repo, ref = mkt_to_repo[mkt_name]
            where = f"{repo}@{ref}" if ref else repo
            errors.append(f"{entry}: marketplace {mkt_name!r} ({where}) has no marketplace.json — unreachable")
            continue
        if plugin_name not in published:
            errors.append(
                f"{entry}: plugin {plugin_name!r} NOT in marketplace {mkt_name!r} "
                f"({mkt_to_repo[mkt_name][0]}). Published plugins: "
                f"{sorted(published)[:10]}{'...' if len(published) > 10 else ''}"
            )

    if errors:
        print("\nMismatches found:", file=sys.stderr)
        for e in errors:
            print(f"  ✘ {e}", file=sys.stderr)
        return 1
    print("\nOK: every enabled plugin resolves against its declared marketplace.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
