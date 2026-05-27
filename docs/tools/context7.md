# context7 — live, version-specific library documentation MCP

**What it does:**
Context7 installs an MCP server that fetches authoritative, version-pinned
documentation for libraries, frameworks, SDKs, CLI tools, and cloud services
directly from upstream sources. Instead of guessing API shapes from training
data, Claude resolves a library identifier and pulls real documentation —
function signatures, configuration options, CLI flags, migration notes, and
worked code samples — at the version you are actually using.

MCP tools exposed:
- `resolve-library-id` — turn a library/framework name into a stable Context7
  identifier (handles aliases, namespaces, and ambiguous names).
- `query-docs` — fetch documentation for the resolved library, optionally
  filtered to a topic or section, with version awareness so React 19 docs
  don't bleed into a React 17 project.

Typical flow: `resolve-library-id("next.js")` then
`query-docs(id, topic="app router")` to ground an answer in current Next.js
App Router behavior rather than whatever the model remembers.

**Why it's in this kit:**
The kit's `CLAUDE.md` treats stale training data as a primary failure mode.
Libraries deprecate methods between minor versions, rename config keys, flip
defaults, and ship breaking migrations on a quarterly cadence. Context7 is
the hedge: it gives Claude a way to verify an API signature against the
current source of truth before generating code that imports it.

The plugin's own MCP-server instruction is explicit: use Context7 whenever
the user asks about a library, framework, SDK, API, CLI tool, or cloud
service — even well-known ones — because training data may not reflect
recent changes. Prefer Context7 over web search for library docs; web
results are noisy and version-mixed, Context7 is version-correct.

**When you'd disable it:**
- Writing a script with zero external dependencies — pure stdlib in any
  language, no SDKs, no frameworks.
- Internal-only codebases where every dependency is an in-house package not
  indexed by Context7.
- Air-gapped environments with no outbound network to the Context7 service.

Do not disable it when you are: integrating any third-party library you have
not used this month, migrating between major versions, or debugging a
"method does not exist" error against an SDK.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `context7`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install context7@anthropics/claude-plugins-official`. The MCP
server runs on demand and talks to the upstream Context7 service; no local
daemon required.

**Cost / footprint:**
- Disk: the plugin itself is a thin MCP wrapper, well under 5 MB.
- Memory: negligible — the server is invoked per-request and exits.
- Network: outbound HTTPS to the Context7 service for every `resolve-library-id`
  and `query-docs` call. Each `query-docs` typically returns a few KB to tens
  of KB of markdown.
- Dependencies: a working network connection to the Context7 service. No
  local model, no daemon, no GPU.
- Latency: one network round-trip per query — usually sub-second, occasionally
  a couple of seconds on large doc fetches.

If the service is unreachable, Context7 calls fail cleanly and you fall back
to whatever the model has in-context. That is strictly worse than a real
lookup, which is why the kit installs it by default.
