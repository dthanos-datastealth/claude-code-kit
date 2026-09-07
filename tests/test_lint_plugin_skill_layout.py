"""Tests for scripts/lint-plugin-skill-layout.py.

The lint's value is entirely in how it resolves a plugin's skills root, so each
of its three resolution rules gets a case here: the top-level-only rule (with
the plugin.json `skills` carve-out), the prune rule, and the namespace rule.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lint-plugin-skill-layout.py"


def _plugin(root: Path, name: str = "p", manifest_extra: dict | None = None) -> Path:
    d = root / name
    (d / ".claude-plugin").mkdir(parents=True)
    manifest = {"name": name, "description": "d", "version": "1.0.0"}
    manifest.update(manifest_extra or {})
    (d / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest))
    return d


def _run(*plugin_dirs: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(p) for p in plugin_dirs]],
        text=True,
        capture_output=True,
    )


def _write(path: Path, text: str = "---\nname: x\ndescription: y\n---\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_flat_skill_file_is_flagged(tmp_path):
    p = _plugin(tmp_path)
    _write(p / "skills" / "foo.md")
    r = _run(p)
    assert r.returncode == 1
    assert "skills/foo.md" in r.stderr
    assert "skills/foo/SKILL.md" in r.stderr, "message must name the fix"


def test_directory_form_passes(tmp_path):
    p = _plugin(tmp_path)
    _write(p / "skills" / "foo" / "SKILL.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr


def test_namespace_level_passes(tmp_path):
    """skills/<ns>/<name>/SKILL.md — the namespace dir is a container, and the
    notion plugin ships exactly this shape."""
    p = _plugin(tmp_path)
    _write(p / "skills" / "ns" / "foo" / "SKILL.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr


def test_vendored_node_modules_skills_are_pruned(tmp_path):
    """A vendored dependency can ship its own flat skills/ tree; it is not the
    plugin's. chrome-devtools-mcp vendors one, and a depth-agnostic walk would
    report that plugin as shipping undiscoverable skills when it ships none."""
    p = _plugin(tmp_path)
    _write(p / "skills" / "real" / "SKILL.md")
    _write(p / "node_modules" / "dep" / "skills" / "vendored.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr
    assert "vendored" not in r.stderr


def test_dot_directory_skills_are_pruned(tmp_path):
    """Agent-tool dot dirs (.agents/, .junie/, .kiro/) can hold their own
    skills/ trees; caveman ships several."""
    p = _plugin(tmp_path)
    _write(p / ".agents" / "skills" / "other.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr


def test_nested_plugin_skills_are_not_the_root(tmp_path):
    """plugins/<name>/skills/ inside a plugin is not the plugin's own root."""
    p = _plugin(tmp_path)
    _write(p / "plugins" / "inner" / "skills" / "flat.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr


def test_manifest_declared_skill_dir_is_not_read_as_a_root(tmp_path):
    """A `skills` manifest entry names a skill DIRECTORY, not another root, so
    the SKILL.md inside it is discoverable. karpathy-skills ships exactly this:
    "skills": ["./skills/karpathy-guidelines"] whose only file is SKILL.md."""
    p = _plugin(tmp_path, manifest_extra={"skills": ["./skills/guidelines"]})
    _write(p / "skills" / "guidelines" / "SKILL.md")
    r = _run(p)
    assert r.returncode == 0, r.stderr


def test_empty_cache_scan_is_not_an_error(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)], text=True, capture_output=True
    )
    assert r.returncode == 0
    assert "nothing to scan" in r.stdout


# ---------- Only frontmatter-bearing flat files are undiscoverable skills ----------
#
# A `skills/` directory can also hold build inputs and prose fragments beside the
# real skill directories. `caveman` ships `skills/native-core.md` next to
# `compile.mjs`, `engine-mcp-tools.json` and `generated/`; it carries no YAML
# frontmatter and was never meant to load. Flagging it is a false positive, and
# a lint that cries wolf about someone else's repo stops being read.
#
# A real skill always opens with a `---` frontmatter block — all six of Berry's
# flat skills did, which is what made them genuine F5 defects. That is the
# discriminator.

def test_flat_md_with_frontmatter_is_flagged(tmp_path):
    """A flat file that really is a skill still fails the lint."""
    p = _plugin(tmp_path, name="withfm")
    (p / "skills").mkdir(parents=True, exist_ok=True)
    (p / "skills" / "berry-plan-and-execute.md").write_text(
        "---\nname: berry-plan-and-execute\ndescription: Verify each plan step.\n---\n\nBody.\n"
    )
    res = _run(p)
    out = res.stdout + res.stderr
    assert res.returncode != 0, out
    assert "berry-plan-and-execute.md" in out


def test_flat_md_without_frontmatter_is_not_a_skill(tmp_path):
    """A frontmatter-less prose fragment under skills/ is a build input."""
    p = _plugin(tmp_path, name="nofm")
    (p / "skills").mkdir(parents=True, exist_ok=True)
    (p / "skills" / "native-core.md").write_text(
        "Build simplest complete system. Trace behavior and invariants before editing.\n"
    )
    (p / "skills" / "real-skill").mkdir()
    (p / "skills" / "real-skill" / "SKILL.md").write_text(
        "---\nname: real-skill\ndescription: A real one.\n---\n\nBody.\n"
    )
    res = _run(p)
    assert res.returncode == 0, (
        "frontmatter-less fragment flagged as an undiscoverable skill:\n"
        + res.stdout + res.stderr
    )
