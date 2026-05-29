#!/usr/bin/env python3
"""UNION-on-conflict merger for ~/.claude/settings.json upgrades.

Replaces scripts/merge-settings.py (which REPLACES dict-typed keys, losing
any user-added entries). This merger reads scripts/merge-policy.json and
applies per-key strategy. User-added top-level keys not in the policy are
preserved verbatim.

Usage:
    intelligent_settings_merge.py <kit-template> <user-settings>
                                  [--policy <merge-policy.json>]

Behavior:
  * Reads kit template (required) and user file (defaults to {} if absent).
  * Per-key merge per policy: union_dict + user-wins, scalar_user_wins_if_set,
    or preserve_user.
  * Atomic write via tmpfile + os.replace.
  * Idempotent: re-running with same inputs produces byte-identical output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_POLICY = Path(__file__).parent / "merge-policy.json"


def union_dict(kit_val: dict, user_val: dict, winner: str) -> dict:
    """Union two dicts; on key conflict, prefer `winner` ("user" or "kit")."""
    if winner == "user":
        return {**kit_val, **user_val}
    return {**user_val, **kit_val}


def scalar_user_wins_if_set(kit_val, user_val, user_has_key: bool):
    """If user has the key set, take user's; else take kit's."""
    return user_val if user_has_key else kit_val


def apply_policy(kit: dict, user: dict, policy: dict) -> dict:
    """Apply per-key merge policy. Returns merged dict."""
    merged = dict(user)  # start from user — preserves unknown keys
    policies = policy.get("policies", {})
    default = policy.get("default_strategy_for_unlisted_keys", {})

    # Apply per-key policies
    for key, rule in policies.items():
        strategy = rule.get("strategy")
        if strategy == "union_dict":
            kit_val = kit.get(key, {})
            user_val = user.get(key, {})
            if not isinstance(kit_val, dict) or not isinstance(user_val, dict):
                # Policy mismatch — fall back to preserve_user
                if key in user:
                    merged[key] = user[key]
                elif key in kit:
                    merged[key] = kit[key]
                continue
            merged[key] = union_dict(kit_val, user_val, rule.get("winner_on_conflict", "user"))
        elif strategy == "scalar_user_wins_if_set":
            user_has = key in user
            merged[key] = scalar_user_wins_if_set(kit.get(key), user.get(key), user_has)
            if merged[key] is None:
                # Neither user nor kit set it — drop the key entirely
                merged.pop(key, None)
        elif strategy == "preserve_user":
            # Keep user's value if present; otherwise omit
            if key in user:
                merged[key] = user[key]
        else:
            # Unknown strategy — fall back to preserve_user for safety
            if key in user:
                merged[key] = user[key]

    # Kit keys not in policy: explicitly NOT introduced (per default
    # "preserve_user" strategy declared in merge-policy.json). If a future
    # default beyond "preserve_user" becomes needed, add the handler here.
    return merged


def atomic_write(path: Path, data: dict) -> None:
    """Write data as JSON to path atomically (tmpfile + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        import contextlib
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit_template", type=Path)
    parser.add_argument("user_settings", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)

    if not args.kit_template.exists():
        print(f"error: kit template not found: {args.kit_template}", file=sys.stderr)
        return 2
    if not args.policy.exists():
        print(f"error: merge policy not found: {args.policy}", file=sys.stderr)
        return 2

    kit = json.loads(args.kit_template.read_text())
    user = json.loads(args.user_settings.read_text()) if args.user_settings.exists() else {}
    policy = json.loads(args.policy.read_text())

    merged = apply_policy(kit, user, policy)
    atomic_write(args.user_settings, merged)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
