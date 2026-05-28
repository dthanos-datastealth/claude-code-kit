import json
from tests.helpers import run_install


def test_settings_merge_preserves_user_env_block():
    pre = json.dumps({"env": {"NODE_EXTRA_CA_CERTS": "/etc/ssl/my.pem"}})
    r = run_install(preexisting_settings=pre)
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["env"]["NODE_EXTRA_CA_CERTS"] == "/etc/ssl/my.pem"


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
    assert mps["berry-marketplace"]["source"]["repo"] == "leochlon/hallbayes"


def test_settings_merge_sets_effort_level():
    r = run_install()
    merged = json.loads((r.home / ".claude" / "settings.json").read_text())
    assert merged["effortLevel"] == "max"


def test_settings_merge_creates_when_no_preexisting():
    r = run_install()
    dst = r.home / ".claude" / "settings.json"
    assert dst.exists()
    merged = json.loads(dst.read_text())
    assert "enabledPlugins" in merged
    assert merged["env"] == {}
