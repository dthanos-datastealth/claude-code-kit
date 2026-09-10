#!/usr/bin/env python3
"""Compute structural delta between kit's settings.json and live's.

Usage: diff-settings.py <kit-template> <live-settings>
Output: JSON object with keys: plugins_added, plugins_removed,
  marketplaces_added, marketplaces_removed, env_keys_only_in_live.
Exit 0 if no delta, 1 if any delta — env differences included, which the
README has always promised ("exits 0 when nothing has drifted") and which
the exit-code calculation used to leave out.
"""
import json
import sys
from pathlib import Path


def runtime_env_keys() -> set[str]:
    """Env keys install.sh writes after the merge (scripts/kit-runtime-env-keys.txt).

    Shared with scripts/_kit_env.sh, which writes them, and uninstall.sh,
    which removes them. Reporting them as "only in live" would make every
    stock install look drifted.
    """
    path = Path(__file__).parent / "kit-runtime-env-keys.txt"
    if not path.is_file():
        return set()
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main() -> int:
    kit = json.loads(Path(sys.argv[1]).read_text())
    live = json.loads(Path(sys.argv[2]).read_text())
    kp = set((kit.get("enabledPlugins") or {}).keys())
    lp = set((live.get("enabledPlugins") or {}).keys())
    km = set((kit.get("extraKnownMarketplaces") or {}).keys())
    lm = set((live.get("extraKnownMarketplaces") or {}).keys())
    le = set((live.get("env") or {}).keys())
    ke = set((kit.get("env") or {}).keys())
    # Written by scripts/_kit_env.sh after the merge rather than shipped in
    # the template, so they are the kit's even though they are not in it.
    # Read from the shared list so this cannot drift from the writer.
    ke |= runtime_env_keys()

    delta = {
        "plugins_added_in_live": sorted(lp - kp),
        "plugins_removed_in_live": sorted(kp - lp),
        "marketplaces_added_in_live": sorted(lm - km),
        "marketplaces_removed_in_live": sorted(km - lm),
        # Only the keys the user added. Reporting the kit's own here made a
        # stock install look drifted and buried the entries that are actually
        # the reader's to account for.
        "env_keys_only_in_live": sorted(le - ke),
    }
    has_delta = any(delta.values())
    print(json.dumps(delta, indent=2))
    return 1 if has_delta else 0


if __name__ == "__main__":
    raise SystemExit(main())
