import json
from tests.helpers import run_install


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
    assert len(plugins) == 21


def test_settings_merge_adds_marketplaces():
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    mps = merged["extraKnownMarketplaces"]
    assert mps["berry-marketplace"]["source"]["repo"] == "dthanos-datastealth/hallbayes"


def test_settings_merge_sets_effort_level():
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["effortLevel"] == "max"


def test_settings_merge_creates_when_no_preexisting():
    """Fresh install (no prior user settings.json): env should be the kit's
    default env block (currently just UV_NATIVE_TLS=1), not empty."""
    r = run_install()
    dst = r.home / ".claude" / "settings.json"
    assert dst.exists()
    merged = json.loads(dst.read_text())
    assert "enabledPlugins" in merged
    assert merged["env"] == {"UV_NATIVE_TLS": "1"}
