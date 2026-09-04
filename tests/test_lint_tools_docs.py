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


def test_source_without_a_locator_fails():
    """A Source section that exists but names nothing leaves the reader with no
    way to obtain the tool — how the dual-graph MCP shipped documented but
    unobtainable while satisfying the section schema."""
    bad = GOOD.replace(
        "**Source:**\ngithub.com/foo/foo",
        "**Source:**\nNOT bundled with this kit — follow the upstream project's\n"
        "setup instructions, then register it with `claude mcp add`.",
    )
    r = run_one(bad)
    assert r.returncode == 1
    assert "names no locator" in r.stderr


def test_bare_domain_locator_passes():
    """The existing fixture's `github.com/foo/foo` has no scheme; requiring
    https:// would fail 22 shipped docs for no reader benefit."""
    r = run_one(GOOD)
    assert r.returncode == 0, r.stderr


def test_full_url_locator_passes():
    r = run_one(GOOD.replace("github.com/foo/foo", "<https://github.com/foo/foo>"))
    assert r.returncode == 0, r.stderr


def test_locator_is_only_looked_for_inside_the_source_section():
    """A URL elsewhere in the doc must not satisfy the Source requirement."""
    bad = GOOD.replace(
        "**Source:**\ngithub.com/foo/foo", "**Source:**\nfollow upstream instructions"
    ).replace("Does foo things.", "Does foo things. See github.com/foo/elsewhere.")
    r = run_one(bad)
    assert r.returncode == 1
    assert "names no locator" in r.stderr
