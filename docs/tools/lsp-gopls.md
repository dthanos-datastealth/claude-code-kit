# lsp-gopls — Go language server via LSP MCP

**What it does:**
The `gopls-lsp` plugin wires the official Go language server (`gopls`) into
Claude's LSP MCP tooling, so requests like "find every caller of `Authn`",
"jump to the definition of `User.Save`", or "what type does this expression
have?" resolve through real Go compiler intelligence rather than string
matching. The plugin activates automatically when the current working file is
a `.go` file.

LSP operations the plugin exposes through the standard MCP LSP interface:
- `goToDefinition` — jump from a symbol to where it is declared.
- `findReferences` — every call site or read of a symbol.
- `hover` — type signature, doc comment, and package info for a symbol.
- `documentSymbol` and `workspaceSymbol` — symbol search inside a file or
  across the module.
- `goToImplementation` — for interface methods, find concrete implementers.
- `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls` — walk the call
  graph in either direction.

**Why it's in this kit:**
The kit's `CLAUDE.md` enforces a strict ordering for code lookup: dual-graph
MCP first, LSP second, built-in Grep third, bash grep/find never. LSP is the
right tool when you need precision — `goToDefinition` understands package
scope, import aliases, generics, and method receivers, all things a string
search will get wrong on the first hit. On a Go codebase of any size,
`findReferences` against the language server is the only reliable way to be
sure you have found every call site of a function before changing its
signature.

**When you'd disable it:**
- Repositories with zero Go files — the plugin will sit idle but consume a
  little bit of startup time and process memory; uninstall if you never touch
  Go.
- Environments where `gopls` cannot be installed (no Go toolchain, sandboxed
  runner).
- One-off polyglot debugging sessions where you want all language servers off
  for determinism.

Do not disable it on any repo that contains a Go module you plan to read,
refactor, or extend — the alternative is grep-based exploration of Go code,
which gets type aliases, embedded structs, and interface implementations
wrong with predictable regularity.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `gopls-lsp`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install gopls-lsp@anthropics/claude-plugins-official`.

Prerequisite: the `gopls` binary must be on `PATH`. Install with:

```sh
go install golang.org/x/tools/gopls@latest
```

and confirm with `which gopls`. The plugin will refuse to start cleanly if
the binary is missing.

**Cost / footprint:**
- Disk: the `gopls` binary itself is roughly 80–120 MB; the plugin adds a
  thin MCP wrapper of negligible size.
- Memory: one `gopls` process per Go repository Claude opens, typically
  around 200 MB steady-state. Large monorepos can climb higher as `gopls`
  caches type information.
- CPU: a brief initial indexing pass per repo; subsequent requests are cheap.
- Network: none after install.
- Dependencies: a working Go toolchain capable of running `gopls` (Go 1.21+
  recommended; see upstream gopls requirements for the current minimum).
