# Plan: claude-code-kit GitHub Pages site

Branch `feature/pages-site` (off `origin/main` @ 13c492f). PR into `main`.
Published at `https://dthanos-datastealth.github.io/claude-code-kit/`.

## Goal

A single designed landing page that continues the visual language of the demo
video (CRT boot intro, synthwave grid, neon teal / magenta / amber, hex section
labels like `0x05 ./install.sh`, a 1977 → 2026 timeline rail) and explains the
kit through three sections the user chose:

1. **Hero + video + install** — boot sequence, title, embedded demo video, the
   one-command install with a copy button.
2. **Principles + workflow** — the seven principles as the video's chain of
   seven rings; the ten-step loop as the video's ring of steps. Both
   interactive (select a ring / step to read it).
3. **Plugin catalog** — every tool the kit documents, as browsable cards with
   filter-by-text.

Out of scope (user decision): install-pipeline diagram and the by-the-numbers
stat block.

## Evidence the plan rests on

| Claim | Provenance |
|---|---|
| `docs/tools/*.md` (24 files) share a fixed schema: `# name — tagline`, then `**What it does:**`, `**Why it's in this kit:**`, `**When you'd disable it:**`, `**Source:**`, `**Cost / footprint:**` | CONFIRMED-CODE: `scripts/lint-tools-docs.py:20-24` enforces it in CI (`ci.yml`, "Run tools-docs schema lint") |
| Principles are `## N. Title` in `docs/philosophy.md` (N = 1..7), each opening with `**The rule:**` | CONFIRMED-CODE: `docs/philosophy.md:16,61,114,150,204,275,320` |
| Workflow steps are `## Step N: Title` in `docs/workflow.md` (N = 1..10), each with `**What it does:**` and a command paragraph labelled `**Slash command:**` or `**Slash commands:**` (steps 2, 6), possibly multi-line; step 5's reads "none — this is the implementation work itself" and is shown as written | CONFIRMED-CODE: `docs/workflow.md:24,61,128,162,211,250,299,343,377,411` (V round 1) |
| `docs/plans/` and `site/` are not copied to `~/.claude/docs` | CONFIRMED-CODE: `scripts/_kit_docs.sh:12` explicit `TOP_LEVEL_DOCS` list + `docs/tools/*.md` only |
| Install commands (three lines, not one) live only in README's `## Quick install` fenced block | CONFIRMED-CODE: `README.md:258-264`. Parsed at build (not hand-copied) so the site cannot drift; `README.md` added to the Pages trigger paths |
| Video hosted as release asset (user decision) | USER |
| Demo video 9.7 MB, 1080p H.264, frames visually compared to original | MEASURED (this session) |
| Pages deploys from an Actions artifact; job needs `pages: write` + `id-token: write` (+ `contents: read` for checkout), `environment: github-pages`, `concurrency: pages` without cancel; latest majors `upload-pages-artifact@v5`, `deploy-pages@v5`; enable via `POST /repos/{owner}/{repo}/pages` with `build_type=workflow` alone | CONFIRMED-DOC (V round 1: docs.github.com custom-workflows page, deploy-pages README, starter-workflows static.yml, rest-api-description OpenAPI, `gh api` release listings) |

## Design

- **Type:** VT323 (CRT boot text), Space Grotesk (display headings),
  JetBrains Mono (labels, code). Google Fonts, `display=swap`.
- **Palette tokens** on `:root`, sampled from video frames: background
  `#07090d`, teal `#2de0b0`, magenta `#ff3d9a`, violet `#8a6cff`, amber
  `#ffb347`, CRT green `#39ff6a`, text `#d8dde6`, muted `#6b7385`.
  Dark-only by design (the video is dark); still honors the page contract
  with an explicit `body` background.
- **Motifs:** CSS-only perspective grid floor under the hero; CRT scanline +
  vignette overlay on the boot block; hex section labels; a sticky timeline
  rail (1977 · 1985 · 1995 · 2008 · 2021 · 2025 · 2026) that doubles as
  section nav and scroll-progress indicator, like the video's footer.
- **Motion:** boot text types once; rings pulse on focus. All motion
  disabled under `prefers-reduced-motion`. Boot sequence skippable (click /
  key) and never blocks content (content is in the DOM, not injected by the
  animation).
- **Responsive:** phone width works with a 16 px gutter, no horizontal
  scroll; the ring of ten steps becomes a vertical list below 640 px.
- **Accessibility:** rings/steps follow the WAI-ARIA APG tabs pattern:
  `role=tablist` container, `role=tab` buttons with `aria-selected` and
  `aria-controls`, one `role=tabpanel` with `aria-labelledby`, roving
  `tabindex`, Left/Right (Up/Down when `aria-orientation=vertical` below
  640 px) wrap, Home/End; video has `controls`, `playsinline`,
  `preload="metadata"`, a poster frame, and no autoplay with sound.

## Files

| File | Change |
|---|---|
| `site/index.html` | Template: markup + inline CSS/JS; one `<script type="application/json" id="kit-data">__KIT_DATA__</script>` placeholder |
| `site/assets/poster.jpg` | Frame from the video's title card (~0x04), small (<150 KB) |
| Release `site-media` (tag, not a version) | Holds `claude-code-kit-demo.mp4` (the 9.7 MB re-encode). The page's `<video src>` points at its `releases/download/` URL. Nothing in `scripts/`, `tests/`, `install.sh` or `plugins/` reads releases or tags (grep, this session) |
| `scripts/build-site.py` | Stdlib-only. Parses tools / principles / workflow docs into JSON, injects it into the template, writes `_site/` (index.html + poster). Fails non-zero on any parse miss (missing field, wrong count) — fail-closed, never ships a half-empty page |
| `tests/test_build_site.py` | Tests against the REAL docs and REAL script (imported via `importlib`, as `tests/test_intelligent_claude_md_merge.py:380-387` does) |
| `scripts/lint-tools-docs.py` | `source_body` generalised to `section_body(text, header)`; the builder imports it with `REQUIRED_SECTIONS` and `check()` instead of re-declaring the schema |
| `scripts/mutants.json` | Entries that delete the builder's count checks, so the mutation gate proves they can fail |
| `.github/workflows/pages.yml` | On push to `main` (paths: `site/**`, `docs/tools/**`, `docs/philosophy.md`, `docs/workflow.md`, `scripts/build-site.py`, `scripts/lint-tools-docs.py`, `README.md`, `.github/workflows/pages.yml`) + `workflow_dispatch`: build → `upload-pages-artifact@v5` → `deploy-pages@v5` in `environment: github-pages`. Permissions `contents: read`, `pages: write`, `id-token: write`; `concurrency: {group: pages, cancel-in-progress: false}` |
| `.gitignore` | Add `_site/` |
| `README.md` | One line under the intro paragraph linking to the site (the video embed is PR #1, separate) |
| `docs/TRACKER.md` | Iteration entry + V/O findings rows |

## TDD sequence

RED first, each confirmed failing for the right reason (missing module /
assertion, not a typo):

1. `test_tools_parse_every_doc` — parsed tool count == `len(glob docs/tools/*.md)`; every entry has non-empty name, tagline, what, why, source URL.
2. `test_principles_are_seven_in_order` — titles 1..7 in file order, each with non-empty rule text.
3. `test_workflow_is_ten_steps` — 10 steps, each with slash command + summary (plural label and step 5's "none" both read).
3b. `test_install_commands_come_from_readme` — the page's install lines equal README's Quick install block.
4. `test_parse_fails_closed` — a doc copy with a missing `**Why it's in this kit:**` raises / exits non-zero (mutation guard: proves the check can fail).
5. `test_build_writes_site` — lifecycle: build into tmp dir → `index.html` exists, placeholder gone, embedded JSON round-trips and equals the parser output, the video `src` is the release URL; re-run is idempotent (same bytes).
6. `test_markdown_inline_rendered_safely` — backticks/links/bold in doc text become `<code>`/`<a>`/`<strong>`; a raw `<script>` in source text is escaped (JSON embedded with every `<` written as the JSON escape `\u003c`).

GREEN: implement `scripts/build-site.py` minimally. Then build the page.

## Verification

- Full suite (`GITHUB_BASE_REF=main uv run pytest`), shellcheck unaffected,
  `lint-scrubbing.py`, `lint-tools-docs.py`.
- Real render: build locally, serve `_site/` over HTTP, open in Chrome
  (DevTools MCP) — screenshot desktop 1440 px and phone 390 px, every
  section, VIEWED. Click real ring/step buttons and the copy button; play the
  video. Lighthouse accessibility audit.
- Deploy: after merge, enable Pages (source = GitHub Actions) via
  `gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow` — BEFORE
  merge, with the user's go-ahead, so the merge push's run can deploy — run the
  workflow, then load the public URL signed-out and view it.
- V+O on the working tree before commit (V: GitHub Pages / Actions docs,
  font licensing, a11y against WAI-ARIA tabs pattern; O: redundancy,
  duplicated parsing vs existing `lint-tools-docs.py` — reuse its field list
  rather than re-declaring it).

## Risks

- **Release-asset playback:** MEASURED this session. Release `site-media`
  created; asset URL 302s to a CDN serving `application/octet-stream` with
  `accept-ranges: bytes`, and a ranged GET returns 206. A `<video>` on
  `https://example.com` loaded it (1920×1080, 171.0 s) and played 2.8 s in
  3 s. Octet-stream does not block playback in Chrome; Safari/Firefox not yet
  measured — check in the real-render step.
- **Pages enablement** is a repo setting change — done only after the user
  approves the merge.
- **Doc drift:** fail-closed parser means a malformed doc breaks the Pages
  build, not the page. CI's pytest run builds from the real docs (`test_build_writes_site`), so the PR catches it first without a second build step.

## Deviations from this plan, as built

- **Palette.** Final tokens were re-sampled from the video's title card and
  grid frames, then the step numbers, `drwxr-xr-x` column and boot "skip"
  control were raised to pass WCAG AA (Lighthouse accessibility 100):
  `#080a10`, `#22e5b5`, `#ff2e88`, `#8b6dff`, `#ffb03a`, `#3dff6e`,
  `#e6e9f0`, `#8a92a6`.
- **Rail labels.** The rail shows section names (boot, install, principles,
  loop, tools, run) rather than the video's years. It is the page's section
  nav, and the years do not correspond to any section, so as labels they
  would point at nothing.
- **No ring pulse.** Dropped so the boot sequence stays the page's one
  unprompted motion; selected rings glow and hovered rings lift instead.

