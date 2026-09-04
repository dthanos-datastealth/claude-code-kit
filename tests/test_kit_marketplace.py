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


EXPECTED_SKILLS = {"upgrade", "rollback", "status", "fix-notion-mcp-port"}


def test_required_skills_present():
    """Plugin must ship the 4 documented skills, each as skills/<name>/SKILL.md.

    Claude Code discovers plugin skills only at that path; a flat
    skills/<name>.md never loads. scripts/lint-plugin-skill-layout.py enforces
    the same invariant across every installed plugin.
    """
    actual = {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()}
    assert actual == EXPECTED_SKILLS, f"skill set drifted: {actual}"
    assert not list(SKILLS_DIR.glob("*.md")), \
        "a flat *.md directly under skills/ is undiscoverable"


def test_required_scripts_present():
    """Plugin must ship the fix-notion-mcp-port.sh script."""
    assert (SCRIPTS_DIR / "fix-notion-mcp-port.sh").exists()


def test_skills_have_frontmatter():
    """Every skill file must start with YAML frontmatter (--- name ... ---)."""
    skills = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    assert len(skills) == len(EXPECTED_SKILLS), \
        f"expected {len(EXPECTED_SKILLS)} SKILL.md files, found {len(skills)}"
    for skill in skills:
        text = skill.read_text()
        assert text.startswith("---\n"), f"{skill.name} missing frontmatter"
        body = text.split("---\n", 2)
        assert len(body) >= 3, f"{skill.name} frontmatter not closed"
        front = body[1]
        assert "name:" in front, f"{skill.name} frontmatter missing 'name:' field"
        assert "description:" in front, f"{skill.name} frontmatter missing 'description:' field"


def test_plugin_version_is_bumped_past_the_broken_layout():
    """Plugin caches are keyed by version: an unchanged version string means
    existing installs keep the cached copy and /plugin update skips the
    plugin, so the skill-layout fix would reach nobody without a bump."""
    from packaging.version import Version

    version = json.loads(PLUGIN_MANIFEST.read_text())["version"]
    assert Version(version) > Version("1.0.0"), \
        f"version {version} must exceed the 1.0.0 that shipped the flat layout"


def test_marketplace_listed_in_kit_settings():
    """claude/settings.json must include the kit's own marketplace + plugin."""
    settings = json.loads((REPO / "claude" / "settings.json").read_text())
    mps = settings.get("extraKnownMarketplaces", {})
    assert "claude-code-kit" in mps, "kit's own marketplace not registered in settings.json"
    plugins = settings.get("enabledPlugins", {})
    assert plugins.get("claude-code-kit@claude-code-kit") is True, \
        "claude-code-kit plugin not enabled in settings.json"


def test_install_sh_derives_marketplaces_from_settings():
    """install.sh no longer duplicates the marketplace list: it derives it from
    claude/settings.json's extraKnownMarketplaces, so the release channel is
    declared in one file and the two can no longer drift. The kit's own
    marketplace is covered by test_marketplace_listed_in_kit_settings."""
    install_sh = (REPO / "install.sh").read_text()
    assert "extraKnownMarketplaces" in install_sh, \
        "install.sh must read the marketplace list from the settings template"
    assert "MARKETPLACES=(" not in install_sh, \
        "the duplicated array is what drifted; it must not come back"


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


CHANNEL_ENTRIES = ("claude-code-kit", "berry-marketplace")


def _current_branch() -> str:
    """Resolve the branch this checkout represents.

    GITHUB_BASE_REF first: on a pull_request event GITHUB_REF_NAME is
    "<n>/merge" and the checkout is a detached merge commit, so a REF_NAME-keyed
    check would never fire on the promote PR — which is the one PR this test
    exists for. The base ref is the branch the refs must match.
    """
    import os
    import subprocess

    for var in ("GITHUB_BASE_REF", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(var, "").strip()
        if value:
            return value
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO, text=True, capture_output=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""
    return out


def test_channel_refs_match_branch():
    """The kit and Berry entries must be pinned to the branch they ship from.

    Promoting prerelease -> main without flipping these would leave stable
    users pointed at the prerelease channel, so this test is what makes the
    promote PR fail until the refs are updated.
    """
    import pytest

    branch = _current_branch()
    if branch in ("", "HEAD"):
        pytest.skip("branch not resolvable (detached HEAD outside CI)")

    settings = _kit_settings()["extraKnownMarketplaces"]
    for name in CHANNEL_ENTRIES:
        src = settings[name]["source"]
        assert "ref" in src, (
            f"{name}: no ref pins the channel — an entry without one follows the "
            f"default branch silently, which is the drift this test prevents"
        )
        assert src["ref"] == branch, (
            f"{name}: ref={src['ref']!r} but this is the {branch!r} branch"
        )

    marketplace = json.loads(MARKETPLACE.read_text())
    for plugin in marketplace["plugins"]:
        src = plugin["source"]
        if isinstance(src, dict) and "ref" in src:
            assert src["ref"] == branch, (
                f"{plugin['name']}: marketplace.json ref={src['ref']!r} but this "
                f"is the {branch!r} branch"
            )
