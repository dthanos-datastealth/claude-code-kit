#!/usr/bin/env python3
"""Compute structural delta between kit's settings.json and live's.

Usage: diff-settings.py <kit-template> <live-settings>
Output: JSON object with keys: plugins_added, plugins_removed,
  marketplaces_added, marketplaces_removed, env_keys_only_in_live.
Exit 0 if no delta, 1 if any delta.
"""
import json
import sys
from pathlib import Path


def main() -> int:
    kit = json.loads(Path(sys.argv[1]).read_text())
    live = json.loads(Path(sys.argv[2]).read_text())
    kp = set((kit.get("enabledPlugins") or {}).keys())
    lp = set((live.get("enabledPlugins") or {}).keys())
    km = set((kit.get("extraKnownMarketplaces") or {}).keys())
    lm = set((live.get("extraKnownMarketplaces") or {}).keys())
    le = set((live.get("env") or {}).keys())

    delta = {
        "plugins_added_in_live": sorted(lp - kp),
        "plugins_removed_in_live": sorted(kp - lp),
        "marketplaces_added_in_live": sorted(lm - km),
        "marketplaces_removed_in_live": sorted(km - lm),
        "env_keys_only_in_live": sorted(le),
    }
    has_delta = any(delta[k] for k in [
        "plugins_added_in_live", "plugins_removed_in_live",
        "marketplaces_added_in_live", "marketplaces_removed_in_live",
    ])
    print(json.dumps(delta, indent=2))
    return 1 if has_delta else 0


if __name__ == "__main__":
    raise SystemExit(main())
