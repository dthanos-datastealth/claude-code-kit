# notion — Notion workspace, search, and task tracker MCP

**What it does:**
The `notion` plugin installs an MCP server that connects Claude to a Notion
workspace and exposes the full read/write surface: search pages and
databases by keyword, create pages under specific parents, query databases
with natural-language property filters, insert new database rows, and
create tasks with sensible defaults in the user's tasks database.

Bundled skills wrap the common workflows:
- `Notion:search` — keyword search across the workspace.
- `Notion:find` — quick lookup of pages or databases by title.
- `Notion:create-page` — create a page, optionally under a chosen parent.
- `Notion:create-task` — create a task in the tasks database with
  sensible defaults applied.
- `Notion:create-database-row` — insert a row into any database using
  natural-language property values.
- `Notion:database-query` — query a database by name or ID and return
  structured, readable results.
- `Notion:tasks:setup` / `tasks:build` / `tasks:plan` / `tasks:explain-diff` —
  end-to-end task-tracker workflows, including turning a code change into
  a Notion explainer doc and converting a Notion page into an
  implementation plan.

Authentication is handled by two MCP tools — `notion__authenticate` and
`notion__complete_authentication` — on first use; the resulting token is
cached by the plugin for subsequent sessions.

**Why it's in this kit:**
The kit's workflow leans heavily on capturing decisions, plans, and
artifacts somewhere humans can find them later. For teams whose source of
truth is Notion, copying material in and out of the Claude session by hand
is friction that gets skipped. Wiring Notion into the agent removes that
friction: a spec lives in Notion, Claude reads it directly with
`Notion:find`; a decision gets made in chat, Claude pushes it into the
relevant page with `Notion:create-page`; a code change ships, Claude
generates the explainer doc with `Notion:tasks:explain-diff`.

It is also the cleanest way to connect Claude to a team task tracker
without writing a custom integration — `tasks:setup` and `tasks:build` give
you a working task board from natural-language prompts.

**When you'd disable it:**
- Teams not using Notion. The slash commands and skills will fail without
  an authenticated workspace, and there is no value to having dead tools
  registered.
- Air-gapped or offline environments with no outbound network to the
  Notion API.
- Strict-compliance contexts where pushing project material into a
  third-party SaaS workspace is prohibited.

Do not disable it on a project where Notion is already the canonical
location for specs, decisions, or task tracking — the alternative is
manual copy-paste that erodes the kit's "capture decisions immediately"
workflow.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `notion`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install notion@anthropics/claude-plugins-official`. On first
use the plugin runs an OAuth-style flow via `notion__authenticate` /
`notion__complete_authentication`; the resulting credentials are stored by
the plugin so subsequent sessions reconnect transparently.

**Cost / footprint:**
- Disk: the plugin itself is a thin MCP wrapper, well under 5 MB. Cached
  auth credentials add a few KB.
- Memory: negligible — the server is invoked per request.
- Network: outbound HTTPS to the Notion API for every search, fetch,
  create, and query. Payloads are typically small JSON; bulk database
  queries scale with row count.
- Dependencies: a Notion workspace and a user authenticated through the
  plugin's first-run flow. No local model, no daemon, no GPU.
- Latency: one network round-trip per call — usually sub-second; large
  database queries occasionally a couple of seconds.
- Rate limits: the Notion API enforces its own per-integration rate limits;
  high-volume bulk operations may need to be paced.

If the workspace is unreachable or the cached credentials expire, calls
fail fast and the plugin prompts a re-authentication — same fail-fast
philosophy as the other network-backed MCPs in the kit.
