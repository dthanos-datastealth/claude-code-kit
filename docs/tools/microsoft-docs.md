# microsoft-docs — Microsoft Learn search and fetch MCP

**What it does:**
The `microsoft-docs` plugin installs an MCP server that queries Microsoft
Learn — the authoritative documentation surface for Azure, .NET, Microsoft
365, Windows, Power Platform, Bicep, VS Code, and the rest of the Microsoft
ecosystem — and returns structured results plus full-page fetches.

MCP tools exposed:
- `microsoft_docs_search` — keyword search against Microsoft Learn,
  returning up to 10 high-quality content chunks (title, URL, excerpt,
  ~500 tokens each). Use first for a quick, grounded overview.
- `microsoft_code_sample_search` — search for code snippets and worked
  examples; up to 20 results, optionally filtered by language. Use when
  you need a real sample for an Azure SDK call or a .NET API.
- `microsoft_docs_fetch` — fetch a full Microsoft Learn page by URL and
  return it as clean markdown. Use after search when the snippet is
  insufficient — full tutorials, prerequisites, troubleshooting guides.

Bundled skills (`microsoft-docs:microsoft-docs`,
`microsoft-docs:microsoft-code-reference`,
`microsoft-docs:microsoft-skill-creator`) wrap the right tool for the right
question — concept lookup, code reference, or building a new
Microsoft-flavored skill.

**Why it's in this kit:**
The Microsoft surface is unusually large and unusually prone to
hallucinated API signatures: the `.NET` BCL alone is enormous, Azure SDK
naming churns across SKUs and language bindings, and PowerShell modules
get renamed between major versions. The kit's `CLAUDE.md` rule
"evidence before assertions" is hard to honor for Microsoft code without an
authoritative lookup — `microsoft-docs` is that lookup. The
`microsoft-code-reference` skill is explicit about catching hallucinated
methods, wrong signatures, and deprecated patterns before they ship.

It is also a better grounding source than web search for Microsoft topics:
Microsoft Learn is canonical, versioned, and not full of outdated blog
posts.

**When you'd disable it:**
- Non-Microsoft stacks — pure POSIX, JVM-only shops, Apple-only mobile,
  Google Cloud / AWS-only infrastructure, Linux kernel work.
- Air-gapped environments with no outbound network to Microsoft Learn.
- One-off scripts where you are already confident in the API surface and
  want to skip the round-trip.

Do not disable it when you are: writing Azure SDK code, debugging a .NET
exception, configuring Microsoft Graph permissions, or building anything
that imports a `Microsoft.*` namespace.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `microsoft-docs`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install microsoft-docs@anthropics/claude-plugins-official`.
The MCP server runs on demand and talks to the upstream Microsoft Learn
service; no local daemon, no authentication required.

**Cost / footprint:**
- Disk: the plugin itself is a thin MCP wrapper, well under 5 MB.
- Memory: negligible — the server is invoked per request and exits.
- Network: outbound HTTPS to Microsoft Learn for every search, code-sample
  search, and page fetch. Search results are bounded to ~500 tokens per
  chunk; `microsoft_docs_fetch` can return larger payloads (full
  markdown pages, occasionally tens of KB).
- Dependencies: a working network connection to Microsoft Learn. No
  account, no local model, no GPU.
- Latency: one network round-trip per call — usually sub-second.

If the service is unreachable, calls fail cleanly and Claude falls back to
in-context knowledge — strictly worse than a real lookup, which is why the
kit installs this MCP by default for any project touching the Microsoft
stack.
