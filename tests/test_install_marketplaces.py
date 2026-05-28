from tests.helpers import run_install


def test_registers_four_marketplaces():
    r = run_install()
    log = r.claude_log.read_text()
    lines = [ln for ln in log.splitlines() if "marketplace add" in ln]
    assert any("anthropics/claude-plugins-official" in ln for ln in lines)
    assert any("dthanos-datastealth/hallbayes" in ln for ln in lines)
    assert any("multica-ai/andrej-karpathy-skills" in ln for ln in lines)
    assert any("JuliusBrussee/caveman" in ln for ln in lines)
    assert len(lines) == 4
