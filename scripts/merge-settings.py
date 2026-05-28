#!/usr/bin/env python3
"""Merge kit's settings.json into the user's existing one.

Usage: merge-settings.py <kit-template> <user-settings-path>

Behavior:
  * Reads kit template (required).
  * If user file exists, reads it; otherwise starts from {}.
  * Merge rules:
      - Env: kit defaults layered UNDER user overrides. Kit ships
        broadly-needed defaults like UV_NATIVE_TLS=1 (required for
        uvx-based MCP servers behind corporate TLS-intercepting proxies).
        User entries always win on conflict, so a user can override or
        disable any kit default explicitly.
      - Replace user's "enabledPlugins" with kit's (kit is source of truth).
      - Replace user's "extraKnownMarketplaces" with kit's.
      - Replace user's "effortLevel" with kit's.
      - Preserve any other top-level user keys untouched.
  * Writes merged result back to user path, atomically.
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: merge-settings.py <kit-template> <user-settings>", file=sys.stderr)
        return 2

    kit_path = Path(sys.argv[1])
    user_path = Path(sys.argv[2])

    kit = json.loads(kit_path.read_text())
    user = json.loads(user_path.read_text()) if user_path.exists() else {}

    merged = dict(user)  # start from user's content
    # Env: kit defaults layered UNDER user overrides (user wins on conflict).
    kit_env = kit.get("env", {})
    user_env = user.get("env", {})
    merged["env"] = {**kit_env, **user_env}
    merged["enabledPlugins"] = kit["enabledPlugins"]
    merged["extraKnownMarketplaces"] = kit["extraKnownMarketplaces"]
    merged["effortLevel"] = kit["effortLevel"]

    # Atomic write
    user_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=user_path.parent, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(merged, f, indent=2)
            f.write("\n")
        os.replace(tmp, user_path)
    except Exception:
        os.unlink(tmp)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
