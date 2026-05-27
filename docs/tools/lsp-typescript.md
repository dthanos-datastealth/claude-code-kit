# lsp-typescript — TypeScript / JavaScript language server via LSP MCP

**What it does:**
The `typescript-lsp` plugin wires `typescript-language-server` (which fronts
the official `tsserver`) into Claude's LSP MCP tooling, providing real
type-aware symbol intelligence for `.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, and
`.mjs` files. Requests like "find every component that uses this hook",
"jump to the declaration of `UserContext`", or "what type does `props`
resolve to here?" route through the same engine your editor uses, with full
awareness of `tsconfig.json` paths, module resolution, JSX, and generics.

LSP operations available via the MCP interface:
- `goToDefinition`, `findReferences`, `goToImplementation` — precise
  navigation through React components, hooks, and module boundaries.
- `hover` — full inferred type, including generic instantiations.
- `documentSymbol`, `workspaceSymbol` — symbol search inside a file or across
  the project.
- `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls` — call-graph
  traversal that respects `import type`, re-exports, and barrel files.

**Why it's in this kit:**
The kit's `CLAUDE.md` enforces LSP-second ordering after the dual-graph MCP,
and ahead of any grep. For TypeScript that ordering matters even more than
for Go: a TS project typically has dozens of re-exports, barrel files,
declaration merging, and path aliases that turn naive string search into a
guessing game. `findReferences` over the language server is the only reliable
way to confirm you have every caller before changing a type. And `hover` on
inferred values lets Claude reason about types it never had to read out of
source — important for libraries that lean on inference (zod, tRPC,
react-query) rather than explicit annotations.

**When you'd disable it:**
- Repositories with zero TypeScript or JavaScript files.
- Environments without a Node.js runtime, or where global npm installs are
  forbidden.
- One-off polyglot debugging sessions where you want all language servers off
  for determinism.

Do not disable it on any frontend or Node.js codebase you plan to read,
refactor, or extend. The alternative is grep-based exploration of TS code,
which is wrong about identifier scope at least as often as it is right.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `typescript-lsp`

Install via the kit's `install.sh`, which registers the marketplace and runs
`claude plugin install typescript-lsp@anthropics/claude-plugins-official`.

Prerequisite: install the language server and the TypeScript compiler
globally:

```sh
npm install -g typescript-language-server typescript
```

and confirm with `which typescript-language-server`. The plugin will refuse
to start cleanly if either binary is missing.

**Cost / footprint:**
- Disk: roughly 50–100 MB for the two npm packages.
- Memory: one `tsserver` process per workspace, typically 300–600 MB on large
  monorepos. Memory grows with project size and how aggressively
  `incremental`, `composite`, and project references are configured.
- CPU: a noticeable warm-up pass on first request as `tsserver` indexes the
  project; subsequent calls are cheap.
- Network: none after install.
- Dependencies: Node.js (current LTS recommended), and the two npm packages
  above. The plugin itself is a thin MCP wrapper of negligible size.
