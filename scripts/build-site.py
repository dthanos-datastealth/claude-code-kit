#!/usr/bin/env python3
"""Build the project website from the kit's own docs.

Reads docs/tools/*.md, docs/philosophy.md and docs/workflow.md, embeds what it
parsed as JSON in site/index.html, and writes the result to --out (default
_site/). Any doc the parser cannot read stops the build: the site either shows
every tool, principle and step, or it is not published.

Usage: build-site.py [--docs DIR] [--out DIR]
"""
import argparse
import html
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE_SRC = REPO / "site"
REPO_URL = "https://github.com/dthanos-datastealth/claude-code-kit"
DOCS_URL = f"{REPO_URL}/blob/main/docs/"
VIDEO_URL = f"{REPO_URL}/releases/download/site-media/claude-code-kit-demo.mp4"

PRINCIPLE_COUNT = 7
STEP_COUNT = 10

_spec = importlib.util.spec_from_file_location(
    "lint_tools_docs", REPO / "scripts" / "lint-tools-docs.py")
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

# The sections the page shows. Source is reduced to its URL (source_url).
TOOL_FIELDS = {
    "what": "What it does:",
    "why": "Why it's in this kit:",
    "disable": "When you'd disable it:",
    "cost": "Cost / footprint:",
}
assert set(TOOL_FIELDS.values()) <= set(lint.REQUIRED_SECTIONS)


class ParseError(Exception):
    pass


# --- Markdown subset -------------------------------------------------------
# The docs use inline code, bold, italics, links, bullet and numbered lists,
# fenced code and the occasional table. That is all this renders; anything
# else passes through as escaped text, never as markup.

SAFE_SCHEMES = ("http", "https", "mailto")


def _anchor(url: str, label: str) -> str:
    # Callers pass already-escaped text, so a quote is the one character left
    # that could end the attribute early.
    href = url.replace('"', "&quot;")
    return f'<a href="{href}">{label}</a>'


def _emphasis(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", text)


def md_inline(text: str, base: str = DOCS_URL) -> str:
    # Code spans and finished links are set aside as \x00n\x00 so the later
    # passes (escaping, emphasis) never reach inside them. A NUL already in
    # the text would be read as one of those markers.
    if "\x00" in text:
        raise ParseError("NUL byte in doc text")
    held = []

    def hold(fragment: str) -> str:
        held.append(fragment)
        return f"\x00{len(held) - 1}\x00"

    text = re.sub(r"`([^`]+)`",
                  lambda m: hold(f"<code>{html.escape(m.group(1), quote=False)}</code>"),
                  text)
    text = html.escape(text, quote=False)
    # A URL that still holds a code span is left as text: its quotes were
    # never escaped, so it cannot go into an attribute.
    def autolink(m):
        url = m.group(1)
        return m.group(0) if "\x00" in url else hold(_anchor(url, url))

    text = re.sub(r"&lt;(https?://(?:(?!&[lg]t;)[^\s<>])+)&gt;", autolink, text)

    def link(m):
        label, url = _emphasis(m.group(1)), m.group(2)
        if "\x00" in url:
            return m.group(0)
        scheme = re.match(r"([a-z][a-z0-9+.-]*):", url, re.I)
        if scheme and scheme.group(1).lower() not in SAFE_SCHEMES:
            return label
        if not scheme and not url.startswith("#"):
            url = base + url
        return hold(_anchor(url, label))

    text = re.sub(r"\[([^\[\]]+)\]\(([^()\[\]\s]+)\)", link, text)
    text = _emphasis(text)
    # Links hold code spans in their labels, so restore until none are left.
    placeholder = re.compile(r"\x00(\d+)\x00")
    while placeholder.search(text):
        text = placeholder.sub(lambda m: held[int(m.group(1))], text)
    return text


_ITEM = re.compile(r"^(\s*)(?:[-*]|\d+\.)\s+(.*)$")


def md_block(text: str, base: str = DOCS_URL) -> str:
    out, para, items, ordered = [], [], [], False
    lines = text.strip("\n").splitlines()

    def flush():
        nonlocal para, items
        if para:
            out.append(f"<p>{md_inline(' '.join(para), base)}</p>")
        if items:
            tag = "ol" if ordered else "ul"
            lis = "".join(f"<li>{md_inline(' '.join(i), base)}</li>" for i in items)
            out.append(f"<{tag}>{lis}</{tag}>")
        para, items = [], []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            body = "\n".join(lines[i + 1:j])
            out.append(f"<pre><code>{html.escape(body, quote=False)}</code></pre>")
            i = j + 1
            continue
        if stripped.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if not rows:
                raise ParseError("table has no header row")
            head, *body = rows
            th = "".join(f"<th>{md_inline(c, base)}</th>" for c in head)
            trs = "".join(
                "<tr>" + "".join(f"<td>{md_inline(c, base)}</td>" for c in r) + "</tr>"
                for r in body)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")
            continue
        item = _ITEM.match(line)
        if not stripped or stripped == "---":
            flush()
        elif item and not item.group(1):
            if para or (items and ordered != stripped[0].isdigit()):
                flush()
            ordered = stripped[0].isdigit()
            items.append([item.group(2)])
        elif items and line.startswith((" ", "\t")):
            items[-1].append(stripped)
        else:
            if items:
                flush()
            para.append(stripped)
        i += 1
    flush()
    return "".join(out)


# --- Doc parsers -----------------------------------------------------------

def _labelled_paragraph(section: str, label_re: str, where: str, label: str) -> str:
    """The paragraph that starts with a bold label, label removed."""
    m = re.search(rf"^\*\*{label_re}\*\*[ \t]*(.*?)(?:\n[ \t]*\n|\Z)", section,
                  re.M | re.S)
    if not m or not m.group(1).strip():
        raise ParseError(f"{where}: missing **{label}** paragraph")
    return " ".join(m.group(1).split())


def _numbered_sections(text: str, heading_re: str, where: str, count: int) -> list:
    heads = list(re.finditer(heading_re, text, re.M))
    found = [int(m.group(1)) for m in heads]
    if found != list(range(1, count + 1)):
        raise ParseError(f"{where}: expected sections 1..{count} in order, found {found}")
    sections = []
    for k, m in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(text)
        nxt = re.search(r"^## ", text[m.end():end], re.M)
        body = text[m.end():m.end() + nxt.start()] if nxt else text[m.end():end]
        sections.append((int(m.group(1)), m.group(2).strip(), body))
    return sections


def parse_tools(tools_dir: Path) -> list:
    tools = []
    base = DOCS_URL + "tools/"
    for path in sorted(Path(tools_dir).glob("*.md")):
        text = path.read_text()
        errs = lint.check(path.name, text)
        if errs:
            raise ParseError("; ".join(errs))
        name, tagline = lint.TITLE_RE.search(text).group(0)[2:].split(" — ", 1)
        entry = {"slug": path.stem, "name": html.escape(name.strip()),
                 "tagline": md_inline(tagline.strip(), base),
                 "doc_url": f"{base}{path.name}"}
        for key, header in TOOL_FIELDS.items():
            body = lint.section_body(text, header, stops=lint.REQUIRED_SECTIONS)
            entry[key] = md_block(body, base)
        url = re.search(r"https://[^\s>)`]+", lint.source_body(text))
        if not url:
            raise ParseError(f"{path.name}: **Source:** has no https URL")
        entry["source_url"] = html.escape(url.group(0).rstrip(".,"))
        tools.append(entry)
    if not tools:
        raise ParseError(f"{tools_dir}: no tool docs found")
    return tools


def parse_principles(path: Path) -> list:
    text = Path(path).read_text()
    out = []
    for n, title, body in _numbered_sections(
            text, r"^## (\d+)\. (.+)$", path.name, PRINCIPLE_COUNT):
        rule = _labelled_paragraph(body, "The rule:", f"principle {n}", "The rule:")
        out.append({"n": n, "title": title, "rule": md_inline(rule)})
    return out


def parse_workflow(path: Path) -> list:
    text = Path(path).read_text()
    out = []
    for n, title, body in _numbered_sections(
            text, r"^## Step (\d+): (.+)$", path.name, STEP_COUNT):
        where = f"step {n}"
        command = _labelled_paragraph(body, r"Slash commands?:", where, "Slash command:")
        what = _labelled_paragraph(body, "What it does:", where, "What it does:")
        out.append({"n": n, "title": title, "command": md_inline(command),
                    "what": md_inline(what)})
    return out


def parse_install(readme: Path) -> list:
    """The commands in README's `## Quick install` fenced block."""
    text = Path(readme).read_text()
    m = re.search(r"^## Quick install\s*\n+```\w*\n(.*?)\n```", text, re.M | re.S)
    if not m:
        raise ParseError(f"{Path(readme).name}: no fenced block under '## Quick install'")
    lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
    if not lines:
        raise ParseError(f"{Path(readme).name}: '## Quick install' block is empty")
    return lines


# --- Build -----------------------------------------------------------------

def embed_json(data) -> str:
    """JSON safe inside <script>: no '<' survives, so '</script' cannot occur."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")


def build(docs: Path, out: Path, readme: Path = REPO / "README.md") -> None:
    data = {
        "tools": parse_tools(docs / "tools"),
        "principles": parse_principles(docs / "philosophy.md"),
        "workflow": parse_workflow(docs / "workflow.md"),
        "install": parse_install(readme),
    }
    page = (SITE_SRC / "index.html").read_text()
    fills = {"__KIT_DATA__": embed_json(data), "__VIDEO_URL__": VIDEO_URL,
             "__REPO_URL__": REPO_URL,
             "__REPO_LABEL__": REPO_URL.removeprefix("https://")}
    for token, value in fills.items():
        if token not in page:
            raise ParseError(f"site/index.html: placeholder {token} missing")
        page = page.replace(token, value)

    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SITE_SRC / "assets", out / "assets", dirs_exist_ok=True)
    (out / "index.html").write_text(page)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--out", type=Path, default=REPO / "_site")
    args = ap.parse_args(argv)
    try:
        build(args.docs, args.out)
    except ParseError as e:
        print(f"build-site: {e}", file=sys.stderr)
        return 1
    print(f"build-site: wrote {args.out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
