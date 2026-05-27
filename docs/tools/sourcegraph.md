# sourcegraph — cross-repo code search MCP

**What it does:**
The `sourcegraph` plugin installs an MCP server that queries a Sourcegraph
instance — either the public `sourcegraph.com` cloud or a self-hosted
deployment — and returns structured code-search results. Claude can run
keyword, regex, or structural queries across many repositories at once,
read specific files at specific revisions, follow references and symbols
across repo boundaries, and grep over commit history without cloning
anything locally.

Bundled skills make the common flows explicit:
- `sourcegraph:sg-search` — natural-language or keyword search over the
  indexed corpus, returning ranked file hits with snippets.
- `sourcegraph:sg-file` — fetch and summarize a specific file from a
  specific repo and revision, without checking out the repo.
- `sourcegraph:searching-sourcegraph` — guidance skill that picks the right
  query syntax for the question at hand (literal, regex, structural,
  symbol, diff search).

**Why it's in this kit:**
The kit's `CLAUDE.md` ranks dual-graph + LSP first for code navigation, but
both are local — they index the repo you are sitting in. The moment a
question crosses repo boundaries ("which other services call this gRPC
endpoint?", "find every consumer of this Kafka topic across the
monorepo-of-monorepos") local indexes stop helping. Sourcegraph is the
answer: a single query against a federated index that already knows about
every repo your org publishes.

It is also the right tool for exploring an unfamiliar codebase quickly: a
few structural queries reveal architecture and conventions far faster than
cloning and grepping.

**When you'd disable it:**
- Single-repo work where dual-graph + LSP cover the whole question. Adding
  a Sourcegraph round-trip just slows you down.
- Air-gapped or offline environments with no reachable Sourcegraph
  instance.
- Organizations without a Sourcegraph deployment and without permission to
  query `sourcegraph.com` for the relevant code (private code is not on the
  public cloud).

Do not disable it when you are: doing a cross-repo refactor, hunting a
caller of a published API, or onboarding into a new codebase you don't yet
have checked out locally.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `sourcegraph`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install sourcegraph@anthropics/claude-plugins-official`.

Prerequisite: a reachable Sourcegraph instance and, for private code, an
access token. The MCP defaults to the public `sourcegraph.com` endpoint;
point it at your self-hosted instance via the plugin's configuration if
you have one. Authentication is typically a `SRC_ACCESS_TOKEN` environment
variable set in your shell profile.

**Cost / footprint:**
- Disk: the plugin itself is a thin MCP wrapper, well under 5 MB. No local
  index — Sourcegraph hosts the indexing.
- Memory: negligible client-side; the MCP server is invoked per request.
- Network: outbound HTTPS to the configured Sourcegraph instance for every
  search and file fetch. Result payloads are typically small (snippets +
  metadata) but can grow when fetching whole files.
- Dependencies: a Sourcegraph instance (cloud or self-hosted) and, for
  private repos, a valid access token. No local daemon, no GPU.
- Latency: one network round-trip per query — usually sub-second for
  searches, occasionally a couple of seconds for large file fetches or
  expensive structural queries.

If the configured instance is unreachable or unauthenticated, every
Sourcegraph call fails fast — same fail-fast philosophy as the other
network-backed MCPs in the kit.
