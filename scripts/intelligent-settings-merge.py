#!/usr/bin/env python3
"""UNION-on-conflict merger for ~/.claude/settings.json upgrades.

Replaces scripts/merge-settings.py (which REPLACES dict-typed keys, losing
any user-added entries). This merger reads scripts/merge-policy.json and
applies per-key strategy. User-added top-level keys not in the policy are
preserved verbatim.

Usage:
    intelligent-settings-merge.py <kit-template> <user-settings>
                                  [--policy <merge-policy.json>]

Behavior:
  * Reads kit template (required) and user file (defaults to {} if absent).
  * Per-key merge per policy: union_dict (winner is per-key — user for `env`
    and `enabledPlugins`, kit for `extraKnownMarketplaces` so a release channel
    can move), scalar_user_wins_if_set, or preserve_user.
  * Reports any key whose user value the kit reclaims; --dry-run reports
    without writing.
  * Atomic write via tmpfile + os.replace.
  * Idempotent: re-running with same inputs produces byte-identical output.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Shared atomic-write helper (replaces previously-inline tmpfile+os.replace
# duplicated across intelligent-settings-merge.py and intelligent-claude-md-merge.py).
sys.path.insert(0, str(Path(__file__).parent))
from _atomic import atomic_write_json  # noqa: E402

DEFAULT_POLICY = Path(__file__).parent / "merge-policy.json"


def kit_wins(rule: dict) -> bool:
    """True when the kit's value takes priority for this key's conflicts.

    Stated once: `reclaimed_entries` decides what to report and `apply_policy`
    decides what to write, and a disagreement between them would produce a note
    that does not match the merge — worse than no note.
    """
    return rule.get("winner_on_conflict", "user") == "kit"


def union_dict(kit_val: dict, user_val: dict, winner: str) -> dict:
    """Union two dicts; on key conflict, prefer `winner` ("user" or "kit")."""
    if winner == "user":
        return {**kit_val, **user_val}
    return {**user_val, **kit_val}


def scalar_user_wins_if_set(kit_val, user_val, user_has_key: bool):
    """If user has the key set, take user's; else take kit's."""
    return user_val if user_has_key else kit_val


def reclaimed_entries(kit: dict, user: dict, policy: dict) -> list[str]:
    """Sub-keys whose user value the kit overwrites, as human-readable lines.

    Only kit-wins union keys can do this, and only some of those matter to a
    reader. Moving release channel rewrites the kit's own declaration of its own
    marketplace, which is not a loss and should not be announced as one — an
    untouched user switching channel would otherwise see two "replaced" notes
    for changes that took nothing from them, which is how the one note that DOES
    mean "your customization is gone" gets tuned out.

    So the two cases are told apart by where the entry points: same target, the
    kit updated itself; different target, the user had aimed it somewhere else
    and that is now undone. Only the second carries the remedy.
    """
    out: list[str] = []
    for key, rule in (policy.get("policies") or {}).items():
        if rule.get("strategy") != "union_dict" or not kit_wins(rule):
            continue
        kit_val, user_val = kit.get(key), user.get(key)
        if not isinstance(kit_val, dict) or not isinstance(user_val, dict):
            continue
        for name, was in sorted(user_val.items()):
            now = kit_val.get(name)
            if name not in kit_val or now == was:
                continue
            if _same_target(was, now):
                out.append(f"{key}.{name}: updated to {json.dumps(_target(now))}")
            else:
                out.append(
                    f"{key}.{name}: REPLACED YOUR {json.dumps(_target(was))} with the "
                    f"kit's {json.dumps(_target(now))}. The kit owns this name. To keep "
                    f"your own, register it under a different name."
                )
    return out


def _target(entry) -> str:
    """The thing an entry points at, ignoring how it is fetched."""
    src = entry.get("source") if isinstance(entry, dict) else None
    if isinstance(src, dict):
        return str(src.get("repo") or src.get("url") or src.get("path") or src)
    return str(src if src is not None else entry)


def _same_target(a, b) -> bool:
    """True when two entries point at the same place, differing only in how."""
    return _target(a) == _target(b)


def apply_policy(kit: dict, user: dict, policy: dict) -> dict:
    """Apply per-key merge policy. Returns merged dict."""
    merged = dict(user)  # start from user — preserves unknown keys
    policies = policy.get("policies", {})

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
            merged[key] = union_dict(kit_val, user_val,
                                     "kit" if kit_wins(rule) else "user")
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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit_template", type=Path)
    parser.add_argument("user_settings", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change; write nothing")
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

    for line in reclaimed_entries(kit, user, policy):
        print(f"  note: {line}", flush=True)

    merged = apply_policy(kit, user, policy)
    if args.dry_run:
        print("  (dry-run: settings.json not written)", flush=True)
        return 0
    atomic_write_json(args.user_settings, merged)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
