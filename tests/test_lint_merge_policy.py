"""Tests for scripts/lint-merge-policy.py."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINT = REPO / "scripts" / "lint-merge-policy.py"


def _run(*paths: Path) -> subprocess.CompletedProcess:
    args = ["python3", str(LINT)] + [str(p) for p in paths]
    return subprocess.run(args, text=True, capture_output=True)


def test_default_kit_policy_passes():
    """The shipped scripts/merge-policy.json validates cleanly."""
    r = subprocess.run(["python3", str(LINT)], text=True, capture_output=True)
    assert r.returncode == 0, f"kit's own merge-policy.json failed lint: {r.stderr}"


def test_missing_file_fails(tmp_path):
    r = _run(tmp_path / "no-such-file.json")
    assert r.returncode == 1


def test_invalid_json_fails(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json at all }")
    r = _run(p)
    assert r.returncode == 1
    assert "invalid JSON" in r.stderr


def test_missing_format_version_fails(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({
        "description": "x",
        "policies": {"k": {"strategy": "preserve_user"}},
        "default_strategy_for_unlisted_keys": {"strategy": "preserve_user"},
    }))
    r = _run(p)
    assert r.returncode == 1
    assert "format_version" in r.stderr


def test_unknown_strategy_fails(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({
        "format_version": 1,
        "description": "x",
        "policies": {"k": {"strategy": "not-a-real-strategy"}},
        "default_strategy_for_unlisted_keys": {"strategy": "preserve_user"},
    }))
    r = _run(p)
    assert r.returncode == 1
    assert "not-a-real-strategy" in r.stderr


def test_union_dict_requires_winner_on_conflict(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({
        "format_version": 1,
        "description": "x",
        "policies": {"env": {"strategy": "union_dict"}},  # missing winner_on_conflict
        "default_strategy_for_unlisted_keys": {"strategy": "preserve_user"},
    }))
    r = _run(p)
    assert r.returncode == 1
    assert "winner_on_conflict" in r.stderr


def test_empty_policies_fails(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({
        "format_version": 1,
        "description": "x",
        "policies": {},
        "default_strategy_for_unlisted_keys": {"strategy": "preserve_user"},
    }))
    r = _run(p)
    assert r.returncode == 1
