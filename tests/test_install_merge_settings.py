import json
from tests.helpers import REPO, run_install


def test_settings_merge_preserves_user_env_entries():
    """User env entries always survive the merge (kit defaults are layered
    UNDERNEATH user entries — user wins on conflict)."""
    pre = json.dumps({"env": {"NODE_EXTRA_CA_CERTS": "/etc/ssl/my.pem"}})
    r = run_install(preexisting_settings=pre)
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["env"]["NODE_EXTRA_CA_CERTS"] == "/etc/ssl/my.pem"


def test_settings_merge_adds_kit_default_env_when_user_doesnt_have_it():
    """The kit ships UV_NATIVE_TLS=1 as a default — required for uvx-based
    MCP servers (Berry) behind corporate TLS-intercepting proxies. Users
    without it in their existing env should get it from the merge."""
    pre = json.dumps({"env": {"SOME_OTHER_VAR": "x"}})
    r = run_install(preexisting_settings=pre)
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["env"]["UV_NATIVE_TLS"] == "1"
    assert merged["env"]["SOME_OTHER_VAR"] == "x"


def test_settings_merge_user_env_overrides_kit_default():
    """If a user explicitly sets a kit-default env var to a different value,
    the user's value wins."""
    pre = json.dumps({"env": {"UV_NATIVE_TLS": "0"}})  # user wants it OFF
    r = run_install(preexisting_settings=pre)
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["env"]["UV_NATIVE_TLS"] == "0", (
        "user's explicit env value must override the kit's default"
    )


def test_settings_merge_adds_enabled_plugins():
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    plugins = merged["enabledPlugins"]
    assert plugins["superpowers@claude-plugins-official"] is True
    assert plugins["berry@berry-marketplace"] is True
    assert plugins["claude-code-kit@claude-code-kit"] is True
    assert len(plugins) == 22


def test_settings_merge_adds_marketplaces():
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    mps = merged["extraKnownMarketplaces"]
    assert mps["berry-marketplace"]["source"]["repo"] == "dthanos-datastealth/hallbayes"


def test_settings_merge_sets_effort_level():
    """Read the expected value from the kit template rather than pinning a
    literal, so the assertion tracks the template instead of re-pinning it."""
    from pathlib import Path

    kit = json.loads(
        (Path(__file__).resolve().parents[1] / "claude" / "settings.json").read_text()
    )
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["effortLevel"] == kit["effortLevel"]


def test_settings_merge_creates_when_no_preexisting():
    """Fresh install (no prior user settings.json): env carries the kit's
    template defaults, not an empty block.

    Asserts containment rather than equality. install.sh also records
    machine-specific runtime keys after the merge — PATH and
    CLAUDE_CODE_ENABLE_TODO_TOOLS, see scripts/_kit_env.sh — and an equality
    assertion here would fail every time that set changes while telling you
    nothing about the merge, which is what this test is for. The runtime keys
    have their own coverage in tests/test_install_env_path.py.
    """
    kit = json.loads((REPO / "claude" / "settings.json").read_text())
    r = run_install()
    dst = r.home / ".claude" / "settings.json"
    assert dst.exists()
    merged = json.loads(dst.read_text())
    assert "enabledPlugins" in merged
    for key, value in kit["env"].items():
        assert merged["env"][key] == value, f"kit env default {key} lost in merge"
