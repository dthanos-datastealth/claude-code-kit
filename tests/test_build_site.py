"""The project website is generated from the kit's own docs.

Every test here runs the real build script against the real docs, so a doc
edit that the site can no longer read fails CI instead of shipping a page
with a hole in it.
"""
import json
import re
import shutil
import subprocess

import pytest

from tests.helpers import REPO, SESSION_TMP

SCRIPT = REPO / "scripts" / "build-site.py"


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_site", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _embedded_data(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" id="kit-data">(.*?)</script>',
        html, re.S)
    assert m, "page has no embedded kit-data block"
    return json.loads(m.group(1))


def test_tools_parse_every_doc():
    mod = _load()
    tools = mod.parse_tools(REPO / "docs" / "tools")
    files = sorted((REPO / "docs" / "tools").glob("*.md"))
    assert [t["slug"] for t in tools] == [f.stem for f in files]
    for t in tools:
        for field in ("name", "tagline", *mod.TOOL_FIELDS):
            assert t[field].strip(), f"{t['slug']}: empty {field}"
        assert t["source_url"].startswith("https://"), t["slug"]

    # A bold sub-heading inside a section is body text, not the end of it:
    # spec-kit's Cost section runs on into "Relationship to /feature-dev".
    spec_kit = next(t for t in tools if t["slug"] == "spec-kit")
    assert "Relationship to" in spec_kit["cost"]


def test_principles_are_seven_in_order():
    mod = _load()
    principles = mod.parse_principles(REPO / "docs" / "philosophy.md")
    assert [p["n"] for p in principles] == list(range(1, 8))
    assert principles[0]["title"] == "Evidence before assertions"
    for p in principles:
        assert p["rule"].strip(), f"principle {p['n']} has no rule text"


def test_workflow_is_ten_steps():
    mod = _load()
    steps = mod.parse_workflow(REPO / "docs" / "workflow.md")
    assert [s["n"] for s in steps] == list(range(1, 11))
    assert steps[0]["title"] == "Brainstorm"
    for s in steps:
        assert s["command"].strip(), f"step {s['n']} has no slash command"
        assert s["what"].strip(), f"step {s['n']} has no summary"


def test_install_commands_come_from_readme():
    mod = _load()
    assert mod.parse_install(REPO / "README.md") == [
        "gh repo clone dthanos-datastealth/claude-code-kit",
        "cd claude-code-kit",
        "./install.sh",
    ]


def test_install_fails_closed_without_quick_install(tmp_path):
    mod = _load()
    readme = tmp_path / "README.md"
    readme.write_text((REPO / "README.md").read_text().replace(
        "## Quick install", "## Installing"))
    with pytest.raises(mod.ParseError, match="Quick install"):
        mod.parse_install(readme)


def test_parse_fails_closed(tmp_path):
    """A doc missing a required field stops the build; it never renders a
    card with a blank section."""
    mod = _load()
    src = (REPO / "docs" / "tools" / "berry.md").read_text()
    broken = src.replace("**Why it's in this kit:**", "**Why:**")
    assert broken != src
    (tmp_path / "berry.md").write_text(broken)
    with pytest.raises(mod.ParseError, match="Why it's in this kit"):
        mod.parse_tools(tmp_path)


def test_parse_fails_closed_on_missing_step(tmp_path):
    mod = _load()
    src = (REPO / "docs" / "workflow.md").read_text()
    broken = src.replace("## Step 7: Review", "## Review")
    assert broken != src
    (tmp_path / "workflow.md").write_text(broken)
    with pytest.raises(mod.ParseError):
        mod.parse_workflow(tmp_path / "workflow.md")


def test_build_writes_site_and_is_idempotent():
    out = SESSION_TMP / "site-build"
    shutil.rmtree(out, ignore_errors=True)

    def build():
        r = subprocess.run(["python3", str(SCRIPT), "--out", str(out)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return (out / "index.html").read_text()

    html = build()
    assert build() == html, "second build produced different bytes"
    for token in ("__KIT_DATA__", "__VIDEO_URL__", "__REPO_URL__", "__REPO_LABEL__"):
        assert token not in html
    assert (out / "assets" / "poster.jpg").is_file()
    assert "\\u0000" not in html and "\x00" not in html
    assert '>github.com/dthanos-datastealth/claude-code-kit</a>' in html

    mod = _load()
    data = _embedded_data(html)
    assert data["tools"] == mod.parse_tools(REPO / "docs" / "tools")
    assert data["principles"] == mod.parse_principles(REPO / "docs" / "philosophy.md")
    assert data["workflow"] == mod.parse_workflow(REPO / "docs" / "workflow.md")
    assert data["install"] == mod.parse_install(REPO / "README.md")
    assert f'src="{mod.VIDEO_URL}"' in html
    assert mod.VIDEO_URL.startswith(
        "https://github.com/dthanos-datastealth/claude-code-kit/releases/download/")


def test_build_exits_nonzero_on_parse_error(tmp_path):
    docs = tmp_path / "docs"
    shutil.copytree(REPO / "docs", docs)
    wf = docs / "workflow.md"
    wf.write_text(wf.read_text().replace("**Slash command:**", "**Command:**", 1))
    r = subprocess.run(["python3", str(SCRIPT), "--docs", str(docs),
                        "--out", str(tmp_path / "out")],
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "Slash command" in r.stderr
    assert not (tmp_path / "out" / "index.html").exists()


def test_markdown_inline_rendered_safely():
    mod = _load()
    html = mod.md_inline("run `a<b` and **bold** and [docs](https://x.test/y) <script>")
    assert "<code>a&lt;b</code>" in html
    assert "<strong>bold</strong>" in html
    assert '<a href="https://x.test/y">docs</a>' in html
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_link_urls_with_query_strings_survive():
    mod = _load()
    html = mod.md_inline("[q](https://x.test/a?b=1&c=2) and <https://x.test/d?e=1&f=2>")
    assert '<a href="https://x.test/a?b=1&amp;c=2">q</a>' in html
    assert '<a href="https://x.test/d?e=1&amp;f=2">https://x.test/d?e=1&amp;f=2</a>' in html


def test_page_embeds_only_the_fields_it_shows():
    mod = _load()
    tool = mod.parse_tools(REPO / "docs" / "tools")[0]
    assert set(tool) == {"slug", "name", "tagline", "what", "why", "disable",
                         "cost", "source_url", "doc_url"}
    assert tool["doc_url"] == f"{mod.REPO_URL}/blob/main/docs/tools/{tool['slug']}.md"


def test_link_hrefs_cannot_break_out_or_run_script():
    mod = _load()
    html = mod.md_inline('<https://x.test/"onmouseover=alert(1)> [x](javascript:alert(1))')
    assert 'href="https://x.test/&quot;onmouseover=alert(1)"' in html
    assert 'href="javascript' not in html


def test_source_url_is_attribute_safe(tmp_path):
    mod = _load()
    src = (REPO / "docs" / "tools" / "berry.md").read_text()
    hostile = 'https://x.test/a?b=1&c="onmouseover=alert(1)'
    doc = src.replace("https://github.com/dthanos-datastealth/hallbayes", hostile, 1)
    assert doc != src
    (tmp_path / "berry.md").write_text(doc)
    url = mod.parse_tools(tmp_path)[0]["source_url"]
    assert url == "https://x.test/a?b=1&amp;c=&quot;onmouseover=alert(1"


def test_emphasis_markup_stays_out_of_link_urls():
    mod = _load()
    html = mod.md_inline("[a](https://x.test/*b*/c) and <https://x.test/**x**>")
    assert '<a href="https://x.test/*b*/c">a</a>' in html
    assert '<a href="https://x.test/**x**">https://x.test/**x**</a>' in html


def test_block_rendering_of_lists_code_and_tables():
    mod = _load()
    html = mod.md_block(
        "Intro line\n\n- one `a`\n  continued\n- two\n\n1. first\n2. second\n\n"
        "```\n<b>raw</b> & more\n```\n\n| H1 | H2 |\n|---|---|\n| a | `b` |\n")
    assert "<p>Intro line</p>" in html
    assert "<ul><li>one <code>a</code> continued</li><li>two</li></ul>" in html
    assert "<ol><li>first</li><li>second</li></ol>" in html
    assert "<pre><code>&lt;b&gt;raw&lt;/b&gt; &amp; more</code></pre>" in html
    assert ("<table><thead><tr><th>H1</th><th>H2</th></tr></thead>"
            "<tbody><tr><td>a</td><td><code>b</code></td></tr></tbody></table>") in html


def test_install_fails_closed_on_empty_block(tmp_path):
    mod = _load()
    readme = tmp_path / "README.md"
    readme.write_text("# x\n\n## Quick install\n\n```bash\n\n```\n")
    with pytest.raises(mod.ParseError, match="empty"):
        mod.parse_install(readme)


def test_code_span_inside_link_label_is_restored():
    mod = _load()
    assert mod.md_inline("[`x`](https://a.test)") == '<a href="https://a.test"><code>x</code></a>'


def test_nul_in_doc_text_is_a_parse_error():
    mod = _load()
    for text in ("a \x000\x00 b", "`\x000\x00`"):
        with pytest.raises(mod.ParseError, match="NUL"):
            mod.md_inline(text)


def test_code_span_in_link_url_cannot_break_out():
    mod = _load()
    for text in ('[a](`"onmouseover=alert(1)//`)',
                 '<https://x.test/`"onmouseover=alert(1)//`>',
                 '[a](`javascript:alert(1)`)'):
        html = mod.md_inline(text)
        assert "<a " not in html, html


def test_adjacent_lists_of_different_types_stay_separate():
    mod = _load()
    assert mod.md_block("1. a\n- b") == "<ol><li>a</li></ol><ul><li>b</li></ul>"


def test_ordered_list_then_bullet_list():
    mod = _load()
    assert mod.md_block("1. a\n\n- b") == "<ol><li>a</li></ol><ul><li>b</li></ul>"


def test_table_of_only_separators_is_a_parse_error():
    mod = _load()
    with pytest.raises(mod.ParseError):
        mod.md_block("| --- | --- |")


def test_embedded_json_cannot_close_its_script_tag():
    mod = _load()
    blob = mod.embed_json({"x": "</script><script>alert(1)</script>"})
    assert "</script" not in blob.lower()
    assert json.loads(blob) == {"x": "</script><script>alert(1)</script>"}
