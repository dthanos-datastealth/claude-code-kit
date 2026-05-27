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
