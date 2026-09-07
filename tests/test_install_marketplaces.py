from tests.helpers import run_install


def test_registers_all_kit_marketplaces():
    r = run_install()
    log = r.claude_log.read_text()
    lines = [ln for ln in log.splitlines() if "marketplace add" in ln]
    assert any("anthropics/claude-plugins-official" in ln for ln in lines)
    assert any("dthanos-datastealth/hallbayes" in ln for ln in lines)
    assert any("multica-ai/andrej-karpathy-skills" in ln for ln in lines)
    assert any("JuliusBrussee/caveman" in ln for ln in lines)
    assert any("Optimal-AI/optibot-skill" in ln for ln in lines)
    assert any("dthanos-datastealth/claude-code-kit" in ln for ln in lines)
    assert len(lines) == 6


def test_marketplace_add_form_matches_the_declared_source_kind():
    """`extraKnownMarketplaces` declares each marketplace as a `github` source.

    Claude Code refuses an add whose network source differs in kind from the
    declaration for that name, so a `github`-declared marketplace must be added
    by its `owner/repo` shorthand — the `https://…/repo.git` URL form is a
    different kind and is rejected outright:

        Cannot add marketplace "claude-plugins-official": its network source
        differs from the one declared for it in settings

    Pinning a ref uses `owner/repo@ref`, which keeps the kind. Cloning still
    goes over HTTPS because register_marketplaces exports
    CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1, which is what the URL form was reaching
    for; the shorthand alone would otherwise clone over SSH.
    """
    import json
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    declared = json.loads((repo / "claude" / "settings.json").read_text())
    entries = declared["extraKnownMarketplaces"]
    assert all(e["source"]["source"] == "github" for e in entries.values()), (
        "this test encodes the rule for `github` sources only"
    )

    r = run_install()
    lines = [ln for ln in r.claude_log.read_text().splitlines() if "marketplace add" in ln]
    assert lines, "no marketplace add invocations recorded"

    expected = {
        f"{e['source']['repo']}@{e['source']['ref']}" if e["source"].get("ref")
        else e["source"]["repo"]
        for e in entries.values()
    }
    got = {ln.split("marketplace add", 1)[1].strip().split()[0] for ln in lines}
    assert got == expected, f"added {sorted(got)}, declared {sorted(expected)}"

    for spec in got:
        assert not spec.startswith(("http://", "https://", "git@")), (
            f"{spec!r} is a URL; settings declares a github source, so the add is rejected"
        )
        assert re.fullmatch(r"[\w.-]+/[\w.-]+(@[\w./-]+)?", spec), f"malformed spec {spec!r}"
