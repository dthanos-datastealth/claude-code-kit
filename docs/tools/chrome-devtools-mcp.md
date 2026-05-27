# chrome-devtools-mcp — Chrome DevTools Protocol access for deep browser introspection

**What it does:**
The `chrome-devtools-mcp` plugin exposes the Chrome DevTools Protocol (CDP)
as MCP tools, giving Claude DevTools-grade access to a running Chrome or
Chromium instance: performance traces, network request inspection, console
capture, heap snapshots, Lighthouse audits, device emulation, and direct
JavaScript evaluation in the page context.

Representative tools: `list_pages`, `new_page`, `select_page`,
`navigate_page`, `close_page`, `take_screenshot`, `take_snapshot`,
`take_heapsnapshot`, `evaluate_script`, `click`, `hover`, `drag`, `fill`,
`fill_form`, `type_text`, `press_key`, `upload_file`, `wait_for`,
`list_console_messages`, `get_console_message`, `list_network_requests`,
`get_network_request`, `handle_dialog`, `resize_page`, `emulate`,
`performance_start_trace`, `performance_stop_trace`,
`performance_analyze_insight`, `lighthouse_audit`.

This is the same protocol Chrome DevTools itself runs on — anything you can
inspect in the DevTools UI you can pull through this MCP.

**Why it's in this kit:**
Playwright is the right tool for "walk the user flow and assert what
rendered." Chrome DevTools MCP is the right tool for "explain why this page
is slow." The kit installs both because the kit's `CLAUDE.md` makes
performance and accessibility regressions explicit verification gates for
frontend work, and those gates need DevTools-grade signals: real Largest
Contentful Paint timings, network waterfall analysis, accessibility-tree
audits, heap snapshots for memory-leak debugging, and full Lighthouse
reports.

Bundled skills make this concrete: `chrome-devtools-mcp:debug-optimize-lcp`,
`chrome-devtools-mcp:memory-leak-debugging`, `chrome-devtools-mcp:a11y-debugging`,
and `chrome-devtools-mcp:troubleshooting` walk Claude through the standard
DevTools investigation flows.

**When you'd disable it:**
- Pure backend, CLI, or data work — no browser to introspect.
- Frontend work where Playwright's higher-level API is enough (simple
  navigate-click-assert flows). DevTools MCP is heavier and lower-level;
  reach for it when you need the data Playwright cannot give you.
- Environments where you cannot run Chrome/Chromium with
  `--remote-debugging-port` open (locked-down CI sandboxes, kiosks).

Do not disable it when you are: debugging Core Web Vitals, hunting a
memory leak, auditing accessibility, or diagnosing why a network request
stalls — Playwright alone will not surface those answers.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `chrome-devtools-mcp`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install chrome-devtools-mcp@anthropics/claude-plugins-official`.

Prerequisite: a Chrome or Chromium binary started with the remote-debugging
port open, e.g.

```sh
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/cdp-profile
```

The MCP connects over CDP to that endpoint. Without a target browser
running, every tool call fails with a connection error — see the bundled
`chrome-devtools-mcp:troubleshooting` skill.

**Cost / footprint:**
- Disk: the plugin itself is small (a few MB). Chrome/Chromium is a
  separate install (~300–500 MB) the kit assumes is already present.
- Memory: one Chrome instance, sized like any normal browser session
  (~200–500 MB plus per-tab overhead). Performance traces and heap
  snapshots add transient memory spikes.
- CPU: idle until a tool call runs; trace recording and Lighthouse audits
  are CPU-heavy for the duration of the run.
- Network: the MCP talks to Chrome over a local WebSocket; the page itself
  makes whatever requests the site under test makes.
- Dependencies: a debuggable Chrome/Chromium instance. The MCP does not
  launch the browser for you by default.

Playwright and Chrome DevTools MCP can coexist; they target different
layers of the same problem space. Install both, reach for whichever fits
the question.
