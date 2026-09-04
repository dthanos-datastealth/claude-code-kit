"""Tests for the kit's own .claude-plugin/marketplace.json and the
claude-code-kit plugin scaffold."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
PLUGIN_DIR = REPO / "plugins" / "claude-code-kit"
PLUGIN_MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
SKILLS_DIR = PLUGIN_DIR / "skills"
SCRIPTS_DIR = PLUGIN_DIR / "scripts"


def test_marketplace_json_exists_and_valid():
    assert MARKETPLACE.exists()
    d = json.loads(MARKETPLACE.read_text())
    assert d.get("name") == "claude-code-kit"
    assert d.get("$schema", "").startswith("https://anthropic.com/claude-code/marketplace")
    assert isinstance(d.get("plugins"), list)
    assert len(d["plugins"]) >= 1


def test_marketplace_contains_claude_code_kit_plugin():
    d = json.loads(MARKETPLACE.read_text())
    names = [p["name"] for p in d["plugins"]]
    assert "claude-code-kit" in names


def test_marketplace_plugin_source_is_git_subdir_relative_path():
    d = json.loads(MARKETPLACE.read_text())
    plugin = next(p for p in d["plugins"] if p["name"] == "claude-code-kit")
    src = plugin["source"]
    assert src["source"] in ("git-subdir", ".", "github")
    if src["source"] == "git-subdir":
        assert src.get("path", "").startswith("plugins/claude-code-kit")


def test_plugin_manifest_present_and_valid():
    assert PLUGIN_MANIFEST.exists()
    d = json.loads(PLUGIN_MANIFEST.read_text())
    assert d.get("name") == "claude-code-kit"
    assert "description" in d


def test_required_skills_present():
    """Plugin must ship the 4 documented skills."""
    required = {"upgrade.md", "rollback.md", "status.md", "fix-notion-mcp-port.md"}
    actual = {p.name for p in SKILLS_DIR.glob("*.md")}
    missing = required - actual
    assert not missing, f"missing skills: {missing}"


def test_required_scripts_present():
    """Plugin must ship the fix-notion-mcp-port.sh script."""
    assert (SCRIPTS_DIR / "fix-notion-mcp-port.sh").exists()


def test_skills_have_frontmatter():
    """Every skill file must start with YAML frontmatter (--- name ... ---)."""
    for skill in SKILLS_DIR.glob("*.md"):
        text = skill.read_text()
        assert text.startswith("---\n"), f"{skill.name} missing frontmatter"
        body = text.split("---\n", 2)
        assert len(body) >= 3, f"{skill.name} frontmatter not closed"
        front = body[1]
        assert "name:" in front, f"{skill.name} frontmatter missing 'name:' field"
        assert "description:" in front, f"{skill.name} frontmatter missing 'description:' field"


def test_marketplace_listed_in_kit_settings():
    """claude/settings.json must include the kit's own marketplace + plugin."""
    settings = json.loads((REPO / "claude" / "settings.json").read_text())
    mps = settings.get("extraKnownMarketplaces", {})
    assert "claude-code-kit" in mps, "kit's own marketplace not registered in settings.json"
    plugins = settings.get("enabledPlugins", {})
    assert plugins.get("claude-code-kit@claude-code-kit") is True, \
        "claude-code-kit plugin not enabled in settings.json"


def test_marketplace_listed_in_install_sh():
    """install.sh MARKETPLACES array must include the kit's own marketplace."""
    install_sh = (REPO / "install.sh").read_text()
    assert "dthanos-datastealth/claude-code-kit" in install_sh, \
        "kit's own marketplace not registered in install.sh"


VALID_EFFORT_LEVELS = {"low", "medium", "high", "xhigh"}


def _kit_settings():
    return json.loads((REPO / "claude" / "settings.json").read_text())


def test_effort_level_is_a_valid_value():
    """`max` is not accepted by the effortLevel key; managed settings drop an
    invalid key with a validation error, so an invalid template value would be
    silently lost org-wide. `max` is session-only, via /effort."""
    level = _kit_settings().get("effortLevel")
    assert level in VALID_EFFORT_LEVELS, (
        f"effortLevel={level!r} is not one of {sorted(VALID_EFFORT_LEVELS)}"
    )


def test_marketplace_sources_are_github_with_optional_ref():
    """install.sh derives its marketplace list from these entries, so every
    source must carry the shape that derivation understands."""
    for name, entry in _kit_settings()["extraKnownMarketplaces"].items():
        src = entry.get("source", {})
        assert src.get("source") == "github", f"{name}: unsupported source type {src!r}"
        assert re.fullmatch(r"[^/\s]+/[^/\s]+", src.get("repo", "")), \
            f"{name}: repo must be owner/name, got {src.get('repo')!r}"
        assert set(src) <= {"source", "repo", "ref"}, f"{name}: unexpected source keys {set(src)}"


def test_enabled_plugin_keys_name_a_registered_marketplace():
    d = _kit_settings()
    known = set(d["extraKnownMarketplaces"])
    for key in d["enabledPlugins"]:
        assert "@" in key, f"{key}: enabledPlugins keys are name@marketplace"
        assert key.split("@", 1)[1] in known, f"{key}: marketplace not registered"
