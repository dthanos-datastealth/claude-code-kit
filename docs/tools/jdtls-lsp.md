# jdtls-lsp — Java language server (Eclipse JDT.LS)

**What it does:**
Wraps Eclipse JDT.LS (`jdtls`) as an MCP-exposed LSP server. Provides
`goToDefinition`, `findReferences`, `hover`, `documentSymbol`,
`workspaceSymbol`, `goToImplementation`, and full call-hierarchy
queries against any `.java` source under Maven, Gradle, or plain
classpath project layouts.

**Why it's in this kit:**
The kit's MANDATORY code-search order is dual-graph → LSP → Read/Grep.
For Java, that means JDT.LS is what answers the precise-symbol
questions after dual-graph has narrowed the search to a file or
package. JDT.LS understands Java's resolution rules — generic type
arguments, overload resolution, package-private visibility, annotation
processors — none of which grep or simple regex can model accurately.
Without an LSP for Java, you would have to fall back to grep, which
misses symbols across `import static`, generic erasure, and overloaded
methods.

**When you'd disable it:**
Repos with zero Java files. JDT.LS does a non-trivial cold-start
(10–30 seconds on large multi-module Gradle projects), and a steady
~400–700 MB resident set per active workspace — there is no reason to
pay that cost on, say, a pure Python or Go repo.

**Source:**
Plugin: `jdtls-lsp@claude-plugins-official` (in `anthropics/claude-plugins-official`).
Upstream Java language server: <https://github.com/eclipse-jdtls/eclipse.jdt.ls>.
Requires JDK 21 or newer to be on `$PATH`, and the `jdtls` launcher
script also on `$PATH`. macOS install: `brew install openjdk@21 jdtls`.
Linux install: distribution package or download the official tarball
from the JDT.LS releases page and add the launcher script to `$PATH`.

**Cost / footprint:** (numbers are empirical from this kit's usage,
not upstream-published benchmarks)
- One JDT.LS Java process per active project; observed at 400–700 MB
  resident in typical service-class repos, occasionally more on
  monorepos with thousands of classes.
- Cold start: ~10–30 seconds on first open of a non-trivial Gradle
  project in our experience (Maven imports tend to be faster).
  Subsequent queries are sub-second.
- Workspace cache lives under `~/.cache/jdtls/workspace/`; safe to
  delete if it grows too large or gets corrupted.
- JDK 17+ requirement (the server itself runs on a JVM; the Java
  version of the code being analyzed can be older).
- No network access at query time — fully local.
