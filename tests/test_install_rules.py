"""Rule files reach ~/.claude/rules on install, and the override file is never
overwritten once seeded."""
import subprocess
from pathlib import Path

from tests.helpers import run_install

REPO = Path(__file__).resolve().parents[1]
KIT_RULES = [
    "10-kit-core.md", "20-kit-code-search.md", "30-kit-quality-loop.md",
    "40-kit-tracker.md", "50-kit-plugins.md", "60-kit-workflow.md",
]


def _reinstall(r) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(REPO / "install.sh")],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True)


def test_install_creates_every_rule_file():
    r = run_install()
    dst = r.home / ".claude" / "rules"
    assert dst.is_dir(), "install did not create ~/.claude/rules"
    for name in KIT_RULES:
        assert (dst / name).is_file(), f"{name} not installed"
        assert (dst / name).read_text() == (REPO / "claude" / "rules" / name).read_text(), (
            f"{name} does not match the shipped file")


def test_install_seeds_the_override_file():
    r = run_install()
    p = r.home / ".claude" / "rules" / "00-user-overrides.md"
    assert p.is_file(), "override file not seeded"
    assert "yours" in p.read_text().lower()


def test_reinstall_never_overwrites_the_override_file():
    """The whole point of the file is that the kit does not own it."""
    r = run_install()
    p = r.home / ".claude" / "rules" / "00-user-overrides.md"
    p.write_text("# mine\n- always use tabs\n")
    res = _reinstall(r)
    assert res.returncode == 0, res.stderr
    assert "always use tabs" in p.read_text(), "install clobbered the user's overrides"


def test_reinstall_does_refresh_kit_rules():
    """Kit files are the kit's: a local edit is replaced, not preserved."""
    r = run_install()
    p = r.home / ".claude" / "rules" / "10-kit-core.md"
    p.write_text("# tampered\n")
    assert _reinstall(r).returncode == 0
    assert p.read_text() == (REPO / "claude" / "rules" / "10-kit-core.md").read_text(), (
        "a kit rule file was not refreshed on reinstall")
