"""Tests for scripts/intelligent-settings-merge.py — the UNION-on-conflict
upgrade-safe settings.json merger that replaces scripts/merge-settings.py."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MERGER = REPO / "scripts" / "intelligent-settings-merge.py"
POLICY = REPO / "scripts" / "merge-policy.json"
KIT_SETTINGS = REPO / "claude" / "settings.json"


def _run(kit: Path, user: Path, policy: Path = POLICY) -> subprocess.CompletedProcess:
    """Run the merger as a subprocess; return CompletedProcess."""
    return subprocess.run(
        ["python3", str(MERGER), str(kit), str(user), "--policy", str(policy)],
        text=True,
        capture_output=True,
    )


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


@pytest.fixture
def temp_settings(tmp_path):
    """Provide tmp_path / 'settings.json' factory; returns the path."""
    return tmp_path / "settings.json"


def test_case_1_empty_live_yields_clean_install_equivalent(temp_settings):
    """No existing user settings → output equals kit defaults (post-merge)."""
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    kit = json.loads(KIT_SETTINGS.read_text())
    # All kit keys should be present
    assert merged["env"] == kit.get("env", {})
    assert merged["enabledPlugins"] == kit.get("enabledPlugins", {})
    assert merged["extraKnownMarketplaces"] == kit.get("extraKnownMarketplaces", {})
    assert merged["effortLevel"] == kit.get("effortLevel")


def test_case_2_user_custom_plugin_preserved(temp_settings):
    """User has a plugin the kit doesn't ship → upgrade preserves it."""
    _write_json(temp_settings, {
        "enabledPlugins": {
            "my-custom-plugin@my-marketplace": True,
            "sourcegraph@claude-plugins-official": True,
        }
    })
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    # User's custom plugins survive
    assert merged["enabledPlugins"].get("my-custom-plugin@my-marketplace") is True
    assert merged["enabledPlugins"].get("sourcegraph@claude-plugins-official") is True
    # Kit plugins added too
    kit_plugins = json.loads(KIT_SETTINGS.read_text()).get("enabledPlugins", {})
    for k in kit_plugins:
        assert k in merged["enabledPlugins"], f"kit plugin {k} missing after merge"


def test_case_3_user_custom_marketplace_preserved(temp_settings):
    """User has a marketplace the kit doesn't list → upgrade preserves it."""
    _write_json(temp_settings, {
        "extraKnownMarketplaces": {
            "my-internal-marketplace": {"source": {"source": "github", "repo": "myorg/internal"}}
        }
    })
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    assert "my-internal-marketplace" in merged["extraKnownMarketplaces"]
    # Kit marketplaces also present
    kit_mps = json.loads(KIT_SETTINGS.read_text()).get("extraKnownMarketplaces", {})
    for k in kit_mps:
        assert k in merged["extraKnownMarketplaces"], f"kit marketplace {k} missing"


def test_case_4_user_env_var_preserved_kit_default_added(temp_settings):
    """User has NODE_EXTRA_CA_CERTS set → preserved. Kit's UV_NATIVE_TLS added."""
    _write_json(temp_settings, {
        "env": {"NODE_EXTRA_CA_CERTS": "/Users/anyone/.claude/certs/corp.pem"}
    })
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    assert merged["env"]["NODE_EXTRA_CA_CERTS"].endswith("corp.pem"), "user env var lost"
    # If kit ships UV_NATIVE_TLS, it must be present
    kit_env = json.loads(KIT_SETTINGS.read_text()).get("env", {})
    if "UV_NATIVE_TLS" in kit_env:
        assert merged["env"]["UV_NATIVE_TLS"] == kit_env["UV_NATIVE_TLS"]


def test_case_4b_user_env_var_wins_on_conflict(temp_settings):
    """If user explicitly sets a value the kit also sets, user wins."""
    _write_json(temp_settings, {
        "env": {"UV_NATIVE_TLS": "0"}  # user explicitly disables
    })
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    assert merged["env"]["UV_NATIVE_TLS"] == "0", "user env override discarded"


def test_case_6_idempotent_second_run_no_change(temp_settings):
    """Running merger twice produces byte-identical output."""
    _write_json(temp_settings, {
        "enabledPlugins": {"my-custom@my-mp": True},
        "env": {"MY_VAR": "abc"},
    })
    _run(KIT_SETTINGS, temp_settings)
    first = temp_settings.read_text()
    _run(KIT_SETTINGS, temp_settings)
    second = temp_settings.read_text()
    assert first == second, "merger is not idempotent — second run changed output"


def test_unknown_top_level_user_key_preserved(temp_settings):
    """Top-level keys not in the policy are preserved verbatim."""
    _write_json(temp_settings, {
        "myInternalKey": {"foo": "bar"},
        "anotherUserField": [1, 2, 3],
    })
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    assert merged["myInternalKey"] == {"foo": "bar"}
    assert merged["anotherUserField"] == [1, 2, 3]


def test_effort_level_user_wins_if_set(temp_settings):
    """If user has effortLevel set, preserve; otherwise take kit's."""
    _write_json(temp_settings, {"effortLevel": "high"})
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    assert merged["effortLevel"] == "high", "user effortLevel discarded"


def test_effort_level_kit_default_when_user_absent(temp_settings):
    """No user effortLevel → take kit's."""
    _write_json(temp_settings, {"enabledPlugins": {}})
    _run(KIT_SETTINGS, temp_settings)
    merged = json.loads(temp_settings.read_text())
    kit_effort = json.loads(KIT_SETTINGS.read_text()).get("effortLevel")
    if kit_effort:
        assert merged["effortLevel"] == kit_effort
