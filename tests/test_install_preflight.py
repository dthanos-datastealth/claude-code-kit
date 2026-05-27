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
