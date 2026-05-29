#!/usr/bin/env python3
"""DEPRECATED: shim that delegates to scripts/intelligent-settings-merge.py.

The original merge-settings.py REPLACED user enabledPlugins, marketplaces,
and effortLevel keys, which destroyed user state on upgrade. The replacement
intelligent-settings-merge.py applies a per-key policy (defined in
scripts/merge-policy.json) that UNIONs dict-typed keys with user-wins-on-
conflict semantics — preserving user-added plugins / marketplaces while still
adding kit defaults.

Existing callers (install.sh:merge_settings, third-party tooling) continue
to invoke this script with the same `<kit-template> <user-settings>` arg
shape; this shim forwards to intelligent-settings-merge.py + the default
policy. No behavior changes are required of callers.
"""
import os
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: merge-settings.py <kit-template> <user-settings>", file=sys.stderr)
        return 2
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, "intelligent-settings-merge.py")
    policy = os.path.join(here, "merge-policy.json")
    os.execv("/usr/bin/env", ["env", "python3", target,
                              sys.argv[1], sys.argv[2],
                              "--policy", policy])


if __name__ == "__main__":
    raise SystemExit(main())
