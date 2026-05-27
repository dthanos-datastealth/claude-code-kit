import subprocess
import sys
from pathlib import Path
import textwrap

REPO = Path(__file__).resolve().parents[1]
LINT = REPO / "scripts" / "lint-scrubbing.py"


def run(text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), "-"],
        input=text,
        text=True,
        capture_output=True,
    )


def test_clean_text_passes():
    r = run("This is generic content with ~/.claude/ paths and localhost:8080.")
    assert r.returncode == 0, r.stderr


def test_owner_username_path_fails():
    r = run("Bad: /Users/dthanos/.claude/CLAUDE.md")
    assert r.returncode == 1
    assert "/Users/dthanos" in r.stderr


def test_company_name_fails():
    r = run("This product, WebStealth, does X.")
    assert r.returncode == 1
    assert "WebStealth" in r.stderr


def test_email_fails():
    r = run("Contact: daniel.thanos@psyigroup.com")
    assert r.returncode == 1
    assert "psyigroup" in r.stderr


def test_berry_word_passes():
    r = run("Berry is the verification plugin shipped in this kit.")
    assert r.returncode == 0
