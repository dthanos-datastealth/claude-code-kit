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
