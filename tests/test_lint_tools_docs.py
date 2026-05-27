import subprocess
import sys
from pathlib import Path
import textwrap

REPO = Path(__file__).resolve().parents[1]
LINT = REPO / "scripts" / "lint-tools-docs.py"


def run_one(text: str):
    return subprocess.run(
        [sys.executable, str(LINT), "-"],
        input=text, text=True, capture_output=True,
    )


GOOD = textwrap.dedent("""\
    # foo — A tool

    **What it does:**
    Does foo things.

    **Why it's in this kit:**
    Because foo matters.

    **When you'd disable it:**
    Never, foo is great.

    **Source:**
    github.com/foo/foo

    **Cost / footprint:**
    Negligible.
""")


def test_complete_doc_passes():
    r = run_one(GOOD)
    assert r.returncode == 0, r.stderr


def test_missing_section_fails():
    bad = GOOD.replace("**Cost / footprint:**\nNegligible.\n", "")
    r = run_one(bad)
    assert r.returncode == 1
    assert "Cost" in r.stderr or "footprint" in r.stderr


def test_missing_title_fails():
    bad = "\n".join(GOOD.splitlines()[1:])  # drop "# foo — A tool"
    r = run_one(bad)
    assert r.returncode == 1
