# playwright-mcp — browser automation and E2E verification MCP

**What it does:**
The `playwright` plugin installs an MCP server that drives a real browser
(Chromium, Firefox, or WebKit) via the Playwright runtime. Claude can
navigate pages, click, type, fill forms, hover, drag, wait for selectors,
upload files, capture screenshots, snapshot the accessibility tree, run
arbitrary JavaScript in the page, watch console output, and inspect network
requests — all as MCP tool calls.

Representative tools: `browser_navigate`, `browser_click`, `browser_type`,
`browser_fill_form`, `browser_hover`, `browser_select_option`,
`browser_press_key`, `browser_wait_for`, `browser_snapshot`,
`browser_take_screenshot`, `browser_console_messages`,
`browser_network_requests`, `browser_evaluate`, `browser_tabs`,
`browser_navigate_back`, `browser_file_upload`, `browser_handle_dialog`,
`browser_close`.

This is the same Playwright API used in production E2E suites — anything
you can script in `@playwright/test` you can drive interactively through
the MCP.

**Why it's in this kit:**
The kit's `CLAUDE.md` makes UI verification mandatory whenever a change
touches a rendered frontend: golden-path plus at least one edge case, with
visual inspection of the result. Without a browser MCP, that rule degrades
into "claim it works because the tests pass." Playwright closes the gap —
Claude can actually open the page, walk the flow, screenshot the outcome,
and check the console for errors before declaring a frontend change done.

It is also the most reliable way to run repeatable E2E tests from inside a
Claude session: deterministic selectors via the accessibility snapshot,
real network plumbing, and the same browser engine your CI uses.

**When you'd disable it:**
- Pure backend work — APIs, data pipelines, CLIs, infra, ML training. No
  rendered UI to verify.
- Headless servers where installing browser binaries is impossible or
  disallowed.
- Memory-constrained environments where launching a 200–300 MB browser per
  session is unacceptable.

Do not disable it on any project that ships a frontend, even if today's
ticket is "just a CSS tweak." The cost of a stale or broken browser MCP is
discovered the moment you need to verify a regression.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `playwright`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install playwright@anthropics/claude-plugins-official`.

Prerequisite: install Playwright and its browser binaries globally so the
MCP server can locate them:

```sh
npm install -g playwright
npx playwright install
```

`npx playwright install` downloads the actual Chromium / Firefox / WebKit
builds (~500 MB total on first run). Without this step the MCP starts but
every `browser_navigate` call fails with a missing-executable error.

**Cost / footprint:**
- Disk: ~500 MB on first init for the bundled browser binaries (Chromium +
  Firefox + WebKit). The MCP wrapper itself is a few MB.
- Memory: roughly 100–300 MB per active browser process; multi-tab sessions
  scale linearly.
- CPU: idle when no page is loaded; spikes during navigation and JS
  execution like any real browser.
- Network: whatever the page under test requests; the MCP itself talks to a
  local browser over CDP/WebSocket.
- Dependencies: Node.js (current LTS recommended), Playwright npm package,
  and the OS libraries each browser needs (on Linux, the standard set
  installed by `npx playwright install-deps`).

A long-lived session that never closes its browser will hold the memory —
remember to call `browser_close` when finished, or rely on the MCP's
process teardown on shutdown.
