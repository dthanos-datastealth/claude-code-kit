import json
import subprocess
from pathlib import Path

from tests.helpers import REPO

DIFF = REPO / "scripts" / "diff-against-live.sh"


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_exit_zero_when_no_drift(tmp_path):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    # Make live identical to repo
    (home / ".claude" / "CLAUDE.md").write_text((REPO / "claude" / "CLAUDE.md").read_text())
    (home / ".claude" / "settings.json").write_text((REPO / "claude" / "settings.json").read_text())
    proc = subprocess.run(
        ["bash", str(DIFF)],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_env_keys_only_in_live_excludes_the_kits_own(tmp_path):
    """The field name is a promise: keys only in live. It listed every live
    env key, so UV_NATIVE_TLS — shipped by the kit — showed up on a stock
    install as though the user had added it, which makes the report useless
    for its actual job of telling you what is yours."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text((REPO / "claude" / "CLAUDE.md").read_text())
    live = json.loads((REPO / "claude" / "settings.json").read_text())
    live["env"]["MY_OWN"] = "1"
    (home / ".claude" / "settings.json").write_text(json.dumps(live))
    proc = subprocess.run(
        ["bash", str(DIFF)],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    out = proc.stdout + proc.stderr
    assert "MY_OWN" in out, "a genuinely user-added env key must be reported"
    for kit_key in json.loads((REPO / "claude" / "settings.json").read_text())["env"]:
        assert kit_key not in out, (
            f"{kit_key} is shipped by the kit and must not be reported as "
            "only-in-live"
        )


def test_env_drift_alone_sets_the_exit_code(tmp_path):
    """README: 'Exits 0 when nothing has drifted, 1 when something has.'
    has_delta covered plugins and marketplaces only, so an env difference —
    the thing most likely to be hand-edited — reported in the body and
    exited 0."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text((REPO / "claude" / "CLAUDE.md").read_text())
    live = json.loads((REPO / "claude" / "settings.json").read_text())
    live["env"]["MY_OWN"] = "1"
    (home / ".claude" / "settings.json").write_text(json.dumps(live))
    proc = subprocess.run(
        ["bash", str(DIFF)],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 1, "an env-only difference is still drift"


def test_exit_one_when_extra_plugin_in_live(tmp_path):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text((REPO / "claude" / "CLAUDE.md").read_text())
    live_settings = json.loads((REPO / "claude" / "settings.json").read_text())
    live_settings["enabledPlugins"]["new-plugin@somewhere"] = True
    (home / ".claude" / "settings.json").write_text(json.dumps(live_settings))
    proc = subprocess.run(
        ["bash", str(DIFF)],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 1
    out = proc.stdout + proc.stderr
    assert "new-plugin@somewhere" in out
