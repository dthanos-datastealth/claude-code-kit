from tests.helpers import run_install


def test_preflight_fails_when_claude_missing():
    r = run_install(omit_claude_cli=True)
    assert r.returncode != 0
    assert "claude" in (r.stderr + r.stdout).lower()


def test_preflight_passes_when_all_tools_present():
    r = run_install()
    # Returncode 0 only if all later steps also pass; preflight alone
    # passing means the script doesn't exit early during preflight.
    # We assert here that the script does NOT emit a preflight-failure
    # message (which would appear before any other step).
    assert "missing prerequisite" not in r.stderr.lower()


def test_preflight_points_at_a_binary_that_is_on_disk_but_off_path():
    """The reported failure: a prereq installer writes to ~/.local/bin, which
    only exports PATH for its own process, so a later separate ./install.sh
    invocation reports the tool missing even though it is on disk. The message
    must name where it found it and how to fix it."""
    r = run_install(omit_claude_cli=True, seed_claude_in=".local/bin")
    assert r.returncode != 0
    out = r.stderr + r.stdout
    assert "missing prerequisite: claude" in out, "keep the original first line"
    assert ".local/bin" in out, "must name the directory it found the tool in"
    assert "export PATH=" in out, "must give the remedy for the current shell"
    assert "hash -r" not in out, (
        "a fresh bash starts with an empty hash table, so rehashing fixes "
        "nothing here — the PATH entry is what is missing"
    )


def test_preflight_rejects_a_python3_below_the_floor():
    """pyproject declares requires-python >= 3.11 and the lint scripts use
    syntax that needs it, but preflight only ever checked that python3
    exists. A machine with the macOS system 3.9 therefore installed cleanly
    and degraded later and elsewhere: the security-guidance plugin dropped
    its cross-file reviewer with 'the hook is running on 3.9'."""
    r = run_install(python3_version="3.9.6")
    assert r.returncode != 0
    out = r.stderr + r.stdout
    assert "python3" in out
    assert "3.11" in out, "name the floor so the reader knows what to install"


def test_preflight_accepts_a_python3_at_or_above_the_floor():
    """Positive control for the check above: a preflight that rejected every
    python3 must fail this.

    The first version of this asserted
    `"python3" not in stderr or "missing prerequisite" not in stderr`, which
    could not fail — the rejection message reads "python3 is too old" and
    never contains "missing prerequisite", so the second clause was always
    true. A control that controls nothing is the failure mode this file's
    own neighbours are about.
    """
    r = run_install()
    assert r.returncode == 0, r.stderr
    assert "too old" not in r.stderr, r.stderr


def test_preflight_requires_node():
    """caveman's UserPromptSubmit hook runs `node`, so a missing node means
    an error on every single prompt. playwright, chrome-devtools and context7
    need npx. None of the four were ever checked."""
    r = run_install(omit_tools=["node"])
    assert r.returncode != 0
    assert "node" in (r.stderr + r.stdout)


def test_preflight_requires_npx():
    r = run_install(omit_tools=["npx"])
    assert r.returncode != 0
    assert "npx" in (r.stderr + r.stdout)


def test_preflight_gives_no_hint_when_the_tool_is_genuinely_absent():
    """With nothing to find, the message must not invent a location."""
    r = run_install(
        omit_claude_cli=True,
        extra_env={"CCK_PREREQ_SEARCH_DIRS": "/nonexistent-cck-search-dir"},
    )
    assert r.returncode != 0
    out = r.stderr + r.stdout
    assert "missing prerequisite: claude" in out
    assert "export PATH=" not in out, "no remedy when there is nothing to point at"
