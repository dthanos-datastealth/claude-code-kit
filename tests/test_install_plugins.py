from tests.helpers import run_install


EXPECTED_PLUGINS = {
    "playwright@claude-plugins-official",
    "superpowers@claude-plugins-official",
    "code-simplifier@claude-plugins-official",
    "context7@claude-plugins-official",
    "claude-md-management@claude-plugins-official",
    "frontend-design@claude-plugins-official",
    "explanatory-output-style@claude-plugins-official",
    "notion@claude-plugins-official",
    "gopls-lsp@claude-plugins-official",
    "typescript-lsp@claude-plugins-official",
    "jdtls-lsp@claude-plugins-official",
    "feature-dev@claude-plugins-official",
    "security-guidance@claude-plugins-official",
    "huggingface-skills@claude-plugins-official",
    "chrome-devtools-mcp@claude-plugins-official",
    "microsoft-docs@claude-plugins-official",
    "optibot@optimal-ai",
    "remember@claude-plugins-official",
    "berry@berry-marketplace",
    "andrej-karpathy-skills@karpathy-skills",
    "caveman@caveman",
    "claude-code-kit@claude-code-kit",
}


def test_installs_all_expected_plugins():
    r = run_install()
    log = r.claude_log.read_text()
    called = set()
    for ln in log.splitlines():
        if ln.startswith("plugin install "):
            called.add(ln.removeprefix("plugin install ").strip())
    missing = EXPECTED_PLUGINS - called
    extra = called - EXPECTED_PLUGINS
    assert not missing, f"missing plugins: {missing}"
    assert not extra, f"unexpected extra installs: {extra}"
