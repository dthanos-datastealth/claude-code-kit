#!/usr/bin/env python3
"""Validate scripts/merge-policy.json against its schema.

Enforces:
  - Top-level keys: format_version (int=1), description (str),
    policies (dict), default_strategy_for_unlisted_keys (dict).
  - Every value in `policies` is a dict with a "strategy" string that
    is one of the known strategies: union_dict, scalar_user_wins_if_set,
    preserve_user.
  - For union_dict, `winner_on_conflict` must be "user" or "kit".
  - `default_strategy_for_unlisted_keys.strategy` must be one of the known
    strategies (preserve_user is the only sane default; warn otherwise).

Usage: lint-merge-policy.py [<path-to-merge-policy.json>]
Exits 0 if valid, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "merge-policy.json"
KNOWN_STRATEGIES = {"union_dict", "scalar_user_wins_if_set", "preserve_user"}
KNOWN_WINNERS = {"user", "kit"}


def lint(path: Path) -> list[str]:
    errs: list[str] = []
    if not path.exists():
        return [f"{path}: file does not exist"]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path}: invalid JSON — {e}"]

    if data.get("format_version") != 1:
        errs.append(f"{path}: top-level format_version must be 1 (got {data.get('format_version')!r})")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errs.append(f"{path}: top-level description must be a non-empty string")

    policies = data.get("policies")
    if not isinstance(policies, dict) or not policies:
        errs.append(f"{path}: top-level 'policies' must be a non-empty object")
        return errs

    for key, rule in policies.items():
        if not isinstance(rule, dict):
            errs.append(f"{path}: policies.{key} must be an object")
            continue
        strategy = rule.get("strategy")
        if strategy not in KNOWN_STRATEGIES:
            errs.append(
                f"{path}: policies.{key}.strategy {strategy!r} not one of {sorted(KNOWN_STRATEGIES)}"
            )
        if strategy == "union_dict":
            winner = rule.get("winner_on_conflict")
            if winner not in KNOWN_WINNERS:
                errs.append(
                    f"{path}: policies.{key}.winner_on_conflict {winner!r} must be 'user' or 'kit'"
                )

    default = data.get("default_strategy_for_unlisted_keys")
    if not isinstance(default, dict):
        errs.append(f"{path}: top-level 'default_strategy_for_unlisted_keys' must be an object")
    else:
        ds = default.get("strategy")
        if ds not in KNOWN_STRATEGIES:
            errs.append(
                f"{path}: default_strategy.strategy {ds!r} not one of {sorted(KNOWN_STRATEGIES)}"
            )

    return errs


def main() -> int:
    args = sys.argv[1:] or [str(DEFAULT_PATH)]
    all_errs: list[str] = []
    for arg in args:
        all_errs += lint(Path(arg))
    if all_errs:
        for e in all_errs:
            print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
