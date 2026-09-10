# Prerequisites

The kit's `install.sh` configures Claude Code and registers plugins; it does
not install the underlying tools those plugins depend on. This document
catalogues every external prerequisite, with install steps for macOS
(Homebrew) and Linux (apt + alternatives), the version requirement, why the
kit needs it, and a verification command you can run after install.

If you are behind a corporate TLS-intercepting proxy, read
[`docs/corporate-tls.md`](corporate-tls.md) before running any installer —
several of these commands fetch artefacts over HTTPS and will fail without
a configured CA bundle.

---

## 1. `claude` CLI (Anthropic)

**Why this kit needs it:** This is Claude Code itself. The kit's purpose
is to configure it; without `claude` on the `PATH`, there is nothing for
`install.sh` to configure.

**Version requirement:** Current stable release. The kit assumes the
`claude` binary supports `claude mcp add` and reads
`~/.claude/settings.json` and `~/.claude/CLAUDE.md`.

**Install:** Follow the upstream install instructions at the Anthropic
documentation site. The CLI is a self-installer; do not package-manage
it via `brew` or `apt` unless Anthropic publishes an official channel
for your platform.

**Verification:** `claude --version` and `which claude`.

---

## 2. `git`

**Why this kit needs it:** `install.sh` clones plugin marketplaces and the
kit itself; the kit's workflow uses git worktrees for isolated feature
work; commit hygiene is part of the discipline the kit enforces.

**Version requirement:** `git >= 2.30` for full worktree behaviour and
`git switch`.

**macOS:**

```sh
brew install git
```

The system `/usr/bin/git` shipped by Xcode Command Line Tools is also
acceptable, but Homebrew's git is typically newer.

**Linux (Debian/Ubuntu):**

```sh
sudo apt update
sudo apt install -y git
```

**Linux (Fedora/RHEL):**

```sh
sudo dnf install -y git
```

**Linux (Arch):** `sudo pacman -S git`

**Verification:** `git --version` (expect 2.30+).

---

## 3. `gh` (GitHub CLI)

**Why this kit needs it:** The kit's workflow uses `gh` for PR creation,
issue triage, and CI inspection. Several skills (review, finishing a
branch) drive `gh` directly.

**Version requirement:** `gh >= 2.0`. After install, authenticate with
`gh auth login`.

**macOS:**

```sh
brew install gh
gh auth login
```

**Linux (Debian/Ubuntu):**

```sh
# Add GitHub's apt repository per https://cli.github.com/manual/installation
type -p curl >/dev/null || sudo apt install -y curl
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install -y gh
gh auth login
```

**Linux (Fedora/RHEL):** `sudo dnf install -y gh && gh auth login`

**Verification:** `gh --version` and `gh auth status`. The latter should
report a logged-in account with the scopes the kit's PR workflows
require; use `gh auth refresh -s <scope>` if you need to add scopes
(e.g. `read:org`).

---

## 4. `python3` >= 3.11

**Why this kit needs it:** The kit's test suite is pytest-based on Python
3.11 standard library only. Several lint scripts in `scripts/` are
Python. Some installed plugins ship Python tooling (`uv`-managed) that
expects a modern Python interpreter.

**Version requirement:** `python3 >= 3.11`. Earlier versions miss type
syntax used in the lint scripts.

**macOS:**

```sh
brew install python@3.12
export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"
```

**Both lines are required, and the second one is the one people miss.**
Homebrew's `python@3.12` links `python3.12` into the prefix but diverts the
*unversioned* names — `python3`, `pip3` and friends — into the formula's
`libexec/bin`, which is not on your PATH. Homebrew says so in its own
install output —

> Unversioned and major-versioned symlinks `python`, `python3`,
> `python-config`, `pip`, `pip3`, etc. … are installed into
> `/opt/homebrew/opt/python@3.12/libexec/bin`

— so without the `export`, `python3` still resolves to the macOS system
interpreter, which is 3.9. Everything that shells out to `python3` then keeps
using 3.9: the kit's merge step, its lint scripts, and the `security-guidance`
plugin, which quietly drops its cross-file reviewer and tells you only that
"the hook is running on 3.9".

`brew install python3` is the alternative if you would rather have Homebrew
link the unversioned name for you. `python@3.11` also satisfies the floor.

Add the `export` to the shell profile your terminal actually reads — see
[Getting the PATH to stick](#getting-the-path-to-stick) at the end of this
document, which matters more here than it looks.

**Linux (Debian/Ubuntu, 22.04+):**

```sh
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Ubuntu 22.04 ships Python 3.10, which is too old; install 3.11+ from the
deadsnakes PPA:

```sh
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

Ubuntu 24.04+ ships 3.12 by default — the first `apt install` suffices.

**Linux (Fedora/RHEL):** `sudo dnf install -y python3 python3-pip`

**Verification:** `python3 --version` (expect 3.11+). Run it in a **new**
terminal, not the one you just typed the `export` into — the point is to
confirm the profile change took, and a shell that already has the variable
set proves nothing about the next one.

`install.sh` now enforces this floor rather than only checking that `python3`
exists, so a 3.9 interpreter stops the install with the fix rather than
surfacing three plugins later.

---

## 5. `uv` (Astral)

**Why this kit needs it:** `uv` is the Python package and project manager
used by several skills (notably anything that runs `uv tool install` or
`uv run`). It also bootstraps isolated Python environments without
polluting the system interpreter.

**Version requirement:** Current stable release. The skills assume
`uv tool install` and `uv run` behave as documented in the upstream Astral
docs.

**Install (all platforms):**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The script installs `uv` to `~/.local/bin` (or `~/.cargo/bin` on some
configurations); ensure that directory is on your `PATH`.

**macOS Homebrew alternative:** `brew install uv`

**Verification:** `uv --version`. Use `uv self update` to pull the
latest release if your install drifts.

---

## 5b. Node.js (`node` and `npx`)

**Why this kit needs it:** four of the 22 enabled plugins run on Node at
runtime, and one of them runs on *every prompt*:

| Plugin | What needs Node |
|---|---|
| `caveman` | a `UserPromptSubmit` hook that runs `node <hook>.js` |
| `playwright` | MCP server launched with `npx @playwright/mcp` |
| `chrome-devtools-mcp` | MCP server launched with `npx chrome-devtools-mcp` |
| `context7` | npm-cache pre-warm; the server itself is HTTP |

Without Node the install still completes, and then every single prompt
prints `/bin/sh: node: command not found` while three MCP servers sit in
`✘ failed`. `install.sh` now checks for both `node` and `npx` in preflight so
that shows up before the install rather than after it.

**Version requirement:** any current LTS or later. Node 18+ also covers
section 8's `typescript-language-server`.

**macOS:** `brew install node`

**Linux (Debian/Ubuntu):** `sudo apt install -y nodejs npm`, or
[nvm](https://github.com/nvm-sh/nvm) for a recent release.

**Linux (Fedora/RHEL):** `sudo dnf install -y nodejs npm`

**Verification:** `node --version` and `npx --version`.

---

## 6. `ripgrep` and `jq` (comfort tools)

**Why this kit needs them:** `ripgrep` (`rg`) is the fallback search tool
the dual-graph MCP uses when its graph hints are insufficient. `jq` is
used by `scripts/merge-settings.py`'s adjacent shell helpers and by hand
when inspecting `~/.claude/settings.json`. Neither is strictly mandatory,
but workflows feel awkward without them.

**Version requirement:** Any recent release. `ripgrep >= 13` and
`jq >= 1.6` are both more than sufficient.

**macOS:**

```sh
brew install ripgrep jq
```

**Linux (Debian/Ubuntu):**

```sh
sudo apt install -y ripgrep jq
```

**Linux (Fedora/RHEL):** `sudo dnf install -y ripgrep jq`

**Verification:** `rg --version` and `jq --version`.

---

## 7. `gopls` (Go LSP)

**Why this kit needs it:** The kit's `CLAUDE.md` mandates LSP queries
before grep for code navigation in Go files. `gopls` is the Go language
server that backs `goToDefinition`, `findReferences`, `documentSymbol`,
and the call-hierarchy tools the LSP integration exposes.

**Version requirement:** Whatever the current Go release publishes via
`go install golang.org/x/tools/gopls@latest`. The LSP integration
auto-detects.

**Install (all platforms with Go installed):**

```sh
go install golang.org/x/tools/gopls@latest
```

This requires `go` on the `PATH`. If Go itself is not installed:

- **macOS:** `brew install go`
- **Linux (Debian/Ubuntu):** `sudo apt install -y golang-go` (or fetch
  the latest from <https://go.dev/dl/> if the apt version is too old).
- **Linux (Fedora/RHEL):** `sudo dnf install -y golang`

`go install` puts the binary in `$(go env GOPATH)/bin` — `~/go/bin` by
default — which is not on `PATH` on a fresh machine. Add it:

```sh
export PATH="$HOME/go/bin:$PATH"
```

**Verification:** `gopls version` and `which gopls`, in a new terminal. See
[`docs/tools/lsp-gopls.md`](tools/lsp-gopls.md) for the rationale.

---

## 8. `typescript-language-server` and `typescript`

**Why this kit needs it:** Same rationale as `gopls`, but for TypeScript
and JavaScript. The LSP backs the same set of structured queries for
`.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, and `.mjs` files.

**Version requirement:** `typescript-language-server` current, and
**`typescript` pinned to the 5.x line**. Do not take the npm default.

**Install (all platforms, Node from section 5b):**

```sh
npm install -g typescript-language-server typescript@5
```

**Why the pin.** `typescript` now resolves to 7.x, the native port, and 7.x
does not ship `tsserver.js` — the file `typescript-language-server` loads.
Install the default and the language server dies at startup with:

```
Error performing documentSymbol: Request initialize failed with message:
Could not find a valid TypeScript installation. Please ensure that the
"typescript" dependency is installed in the workspace or that a valid
tsserver.path is specified. Exiting.
```

**Verification** — check for the file the server actually needs, not just
that a compiler answers:

```sh
ls "$(npm root -g)/typescript/lib/tsserver.js"   # must exist
typescript-language-server --version
```

`tsc --version` is *not* a sufficient check. It prints happily on 7.x, where
the LSP is completely non-functional — a green check next to a dead
integration, which is the failure mode
[`docs/verification-standards.md`](verification-standards.md) is about.

See [`docs/tools/lsp-typescript.md`](tools/lsp-typescript.md) for the
rationale.

---

## 9. `jdtls` (Eclipse JDT Java LSP)

**Why this kit needs it:** the `jdtls-lsp` plugin shipped in the kit
wraps Eclipse JDT.LS as an MCP-exposed LSP. Without the `jdtls`
launcher (and a JDK 21+ runtime to back it), the plugin loads but
every call falls through.

**Version requirement:** `jdtls` from any recent build, plus
**JDK 21 or newer** as the JVM that runs it. (Upstream Eclipse
JDT.LS requires Java 21 minimum as of late-2025; older JDKs will
refuse to launch the server. The Java version of the code being
analyzed can be older.)

**macOS:**

```sh
brew install openjdk jdtls
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
```

**The `export` is required.** Homebrew's `openjdk` is keg-only — it is not
symlinked into `/opt/homebrew/bin`, so after a completely successful install
`java` still resolves to the macOS stub, which reports:

```
The operation couldn't be completed. Unable to locate a Java Runtime.
```

`brew install jdtls` pulls a current JDK as a dependency, so you generally do
not need to name a version; use `brew install openjdk@21 jdtls` only if you
specifically want 21 on your PATH.

**Linux (Debian/Ubuntu):** install OpenJDK 21 via your package
manager, then download the JDT.LS tarball from the [official
releases page](https://download.eclipse.org/jdtls/snapshots/?d) and
add the launcher script to `$PATH`.

**Verification:**

```sh
java -version        # must print a real version: openjdk 21 or newer
which jdtls          # launcher on PATH
```

`java -version` is the check that matters, and it is the one that actually
fails when this is broken: with no JVM reachable it prints "Unable to locate
a Java Runtime" instead of a version.

Two commands **not** to use:

- `jdtls --help` — `jdtls` is a Python launcher, so `--help` never starts a
  JVM. It exits 0 and prints usage on a machine with no Java at all: a green
  check next to a dead integration.
- `jdtls --version` — this one starts the language server and blocks
  forever. It is not a version probe.

See [`docs/tools/jdtls-lsp.md`](tools/jdtls-lsp.md) for the plugin's
behavior, cost/footprint, and when to disable it.

---

## 10. Dual-graph MCP server (external prerequisite)

**Why this kit needs it:** The kit's mandatory code-navigation order is
dual-graph first, LSP second, grep last. The dual-graph MCP server is
what makes the first leg of that order possible; without it,
`graph_continue` returns nothing and the discipline collapses to
LSP+grep.

**Version requirement:** Whatever the upstream project publishes as
current.

**What satisfies this requirement.** Any MCP server exposing the tool contract
below satisfies `CLAUDE.md`; the kit is not tied to one implementation. The
contract is the requirement, and it is what to check a candidate against:

| Tool | Used by `CLAUDE.md` for |
|---|---|
| `graph_continue` | the mandatory first call for any lookup |
| `graph_scan` | one-time project indexing when `needs_project=true` |
| `graph_read` | reading a recommended file, or `file::symbol` |
| `fallback_rg` | the capped supplementary search |
| `graph_register_edit` | recording edits after a change |
| `graph_add_memory` | writing decisions/facts to the context store |

`graph_continue` must return `needs_project`, `confidence`,
`recommended_files`, `max_supplementary_greps` and `max_supplementary_files`,
because the rules branch on all five.

**Reference implementation: `graperoot`.** The `mcp-graph-server` binary is a
console script of the `graperoot` package on PyPI. Two ways to get it:

```sh
# Reproducible, no auto-updater — what this kit recommends.
uv tool install graperoot        # or: pip install graperoot into a venv
```

That provides `mcp-graph-server` and `mcp-graph-server-stdio`. Upstream's own
documented path is instead a shell installer (`curl … | bash`, PowerShell, or
Scoop) which creates a launcher plus a private venv under `~/.dual-graph/`;
that launcher is the vehicle this kit has actually been run against, and it
self-updates (see below). Pick the PyPI path for a pinned, auditable install;
pick upstream's installer if you want the launcher's extra tooling.

The project ships compiled per-interpreter wheels, and the platform coverage is
narrower than it looks. As published for 3.10.19:

| Python | macOS arm64 | macOS x86_64 | Linux x86_64 | Linux aarch64 | Windows amd64 |
|---|---|---|---|---|---|
| 3.10 | none | none | yes | none | yes |
| 3.11 | `macosx_26_0` | none | yes | none | yes |
| 3.12 | `macosx_26_0` | none | yes | none | yes |
| 3.13 | `macosx_26_0` | none | yes | none | yes |

Three of those gaps bite real fleets. **macOS wheels start at `macosx_26_0`**, so
a Mac on macOS 15 or earlier matches none. **There is no Intel macOS wheel at
all.** **There is no Linux aarch64 wheel**, so a Graviton EC2 instance gets none
either; the x86_64 wheels are `manylinux2014` / `manylinux_2_17`.

Where no wheel matches, pip falls back to building a Cython project from source.
So the PyPI path is clean on Linux x86_64, Windows amd64, and Apple Silicon
running macOS 26+ on Python 3.11-3.13. Anywhere else, prefer upstream's
launcher, which ships its own private venv, or leave the dual-graph leg out.

Confirm your own box before committing to the PyPI path:

```sh
pip download --only-binary=:all: graperoot -d /tmp/gr-probe
```

**Before you adopt it, know what you are adopting.** This is a third-party
dependency with an unusual profile for a code-navigation tool, and the kit is
naming it rather than leaving it unnamed:

- **Proprietary and closed-source.** PyPI reports `License: Proprietary`, and
  the engine ships as compiled Cython wheels. The public repository
  (<https://github.com/kunal12203/Codex-CLI-Compact>) carries the launchers
  under Apache-2.0, not the engine.
- **Self-updating.** Upstream documents that the launcher checks for updates on
  every run and applies them without asking, fetching from its own distribution
  channel and replacing both the launcher scripts and the compiled wheel. That
  is why an installed launcher can report a different version than PyPI
  resolves. Upstream documents `graperoot --no-auto-update` to stop it.
- **Telemetry on by default.** Upstream documents a version check, a heartbeat
  carrying a machine id and platform, a one-time feedback prompt, and anonymous
  crash reports (error type, failing step, OS, Python and tool versions), with
  `graperoot --no-telemetry` to opt out.
- **Both opt-out flags belong to upstream's shell installer, not to the PyPI
  package.** `uv tool install graperoot` installs six executables —
  `context-packer`, `dg-graph`, `dgc-claude`, `graph-builder`,
  `mcp-graph-server`, `mcp-graph-server-stdio` — and **no `graperoot`
  command at all**, so on the path this document recommends there is nothing
  to pass `--no-telemetry` to. If those opt-outs matter to you, that is an
  argument for upstream's launcher, or for substituting a different server
  against the contract above. Do not assume the PyPI install is quiet
  because the flags are documented somewhere.

Do not probe the server with `mcp-graph-server --help`: it does not handle
`--help`, it starts the stdio server and blocks until you kill it.

If that profile is not acceptable for your environment, implement or substitute
any server satisfying the contract above — that is precisely why the contract,
not the package, is the requirement.

See [`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md) for the
rationale and the MCP tools the kit's `CLAUDE.md` rules reference.

**Register with Claude Code (once you have the binary path):**

```sh
# Resolve the binary rather than pasting a path, and fail loudly if it is not
# on PATH — `uv tool install` puts it in ~/.local/bin, which is exactly the
# directory the PATH callout in this document is about, so an unguarded
# substitution here would register an empty path and produce a server that
# never starts.
GS="$(command -v mcp-graph-server)"
test -n "$GS" || { echo "mcp-graph-server not on PATH — see the PATH callout below"; exit 1; }
claude mcp add --scope user dual-graph "$GS" -- --stdio
```

**`--scope user` is load-bearing.** Without it `claude mcp add` registers the
server against the *current project* — you get
`Added stdio MCP server ... to local config` and an entry under
`projects["<cwd>"]` in `~/.claude.json`, not under the top-level
`mcpServers`. The graph then exists only in the directory you happened to run
the command from. Everywhere else `graph_continue` is simply absent, the
first leg of the mandatory search order silently no-ops, and the kit falls
back to the grep it tells you not to use. Nothing announces this, and
`claude mcp list` run from that one directory reports it connected.

If you installed via upstream's launcher instead, the binary lives in that
private venv and is not on `PATH`; pass its absolute path
(`~/.dual-graph/venv/bin/mcp-graph-server`) in place of `"$GS"`.

The kit has been run with two environment variables set on the registration,
which scope the index to a directory tree:

```sh
claude mcp add --scope user dual-graph "$GS" \
  -e DG_DATA_DIR=/path/to/index -e DUAL_GRAPH_PROJECT_ROOT=/path/to/repos -- --stdio
```

Neither name appears in upstream's documented environment list (which covers
`DG_HARD_MAX_READ_CHARS`, `DG_TURN_READ_BUDGET_CHARS`,
`DG_FALLBACK_MAX_CALLS_PER_TURN`, `DG_RETRIEVE_CACHE_TTL_SEC` and
`DG_MCP_PORT`) — they are recorded here because they are what a working
registration uses, not because upstream specifies them.

The `--` separator is required so that `--stdio` is passed as an
argument to the MCP binary rather than parsed by `claude mcp add`
itself.

**Registration is per-HOME as well as per-scope.** With `--scope user` the
entry goes in the top-level `mcpServers` of that HOME's `~/.claude.json`, so
it applies to every project — but only for that HOME. If you use an isolated
`$HOME` for testing (see the README §"Testing the kit in parallel"), repeat
the registration there: `HOME="$TEST_HOME" claude mcp add --scope user
dual-graph /absolute/path -- --stdio`. The binary is shared across HOMEs;
only the registration is not.

**Verification:**

```sh
claude mcp list | grep dual-graph
# Expect: dual-graph: /absolute/path/to/mcp-graph-server --stdio - ✓ Connected

# And confirm it really is user-scoped, not project-scoped:
python3 -c "import json,pathlib; d=json.loads((pathlib.Path.home()/'.claude.json').read_text()); print('user scope:', list(d.get('mcpServers',{})))"
# Expect dual-graph in that list.
```

Two ways this check can lie to you, both worth knowing:

- Run from the one directory where a project-scoped registration exists,
  `claude mcp list` says `✓ Connected` while every other project has
  nothing. The `python3` line above is the one that distinguishes them.
- `claude mcp list` spawns a fresh process, so it reports the server's real
  health — which can differ from *your current session*, where a connection
  that failed earlier stays cached for about 15 minutes. After fixing a PATH
  or a registration, start a new session rather than trusting either signal
  alone.

---

## 11. Berry verifier LLM backend

**Why this kit needs it:** Berry's `audit_trace_budget` and
`detect_hallucination` tools call an OpenAI-compatible LLM backend to
compute the information-theoretic contribution of each evidence span to
each claim. Without a reachable backend, every Berry-gated step fails
because the verifier cannot score the spans.

**Version requirement:** Any OpenAI-compatible HTTP endpoint. The kit
defaults to OpenRouter-hosted `openai/gpt-4o-mini` (configured via
`~/.berry/config.json` + `~/.berry/mcp_env.json`). A self-hosted
`llama-server` from `llama.cpp` is supported as an offline /
air-gapped alternative.

**Install:** Get an OpenRouter API key from <https://openrouter.ai/> and
configure Berry by running the configure skill (see Verification below)
or by editing `~/.berry/config.json` directly. See
[`docs/tools/berry.md`](tools/berry.md) for the full configuration
schema, env-var contract, and the self-hosted alternative.

**Verification:**

The Berry plugin exposes a configuration skill — invoke
`berry:berry-configure` after install and follow its prompts. The skill
probes the configured backend and reports whether it can reach it.

For a manual check against OpenRouter:

```sh
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models | jq '.data | length'
```

A successful response prints a number (the count of available models).
For a manual check against a self-hosted `llama-server` on port 8080:

```sh
curl -s http://127.0.0.1:8080/v1/models | jq .
```

---

## 12. `specify` CLI (spec-kit — optional, per-project)

**Why this kit needs it:** Spec-kit provides an optional spec-driven
alternative to the kit's default brainstorm → plan → TDD flow. See
[`docs/tools/spec-kit.md`](tools/spec-kit.md) for when to choose it
over `/superpowers:brainstorming`. The CLI is not installed by the
kit's `install.sh` because it is per-developer tooling, not part of
the Claude Code surface itself.

**Version requirement:** This kit was last verified against
spec-kit `v0.8.16`. Newer tags should work but the slash-command
names occasionally evolve; pin the version in your install command.

**Install (all platforms, requires `uv` from section 5):**

```sh
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.8.16
```

For corporate-TLS environments, prepend the env vars from
[`docs/corporate-tls.md`](corporate-tls.md):

```sh
SSL_CERT_FILE=/path/to/corporate-ca.pem \
GIT_SSL_CAINFO=/path/to/corporate-ca.pem \
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.8.16
```

**Per-project init (one-time, in the project directory you want
spec-driven flows in):**

```sh
specify init --here --integration claude
```

This writes `.claude/skills/speckit-*/` and `.specify/` into the
current directory. Restart Claude Code in that directory for the
`/speckit-*` slash commands to register.

`--here` prompts for confirmation in any non-empty directory, which every
real project is. Add `--force` to skip the prompt when scripting it:

```sh
specify init --here --force --integration claude
```

**Verification:**

```sh
specify --version                          # specify 0.8.16 (or your pinned version)
ls .claude/skills/ | grep -c speckit       # 14 on 0.8.16
```

The 14 are the nine core commands — `speckit-constitution`,
`speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`,
`speckit-analyze`, `speckit-checklist`, `speckit-implement`,
`speckit-taskstoissues` — plus five git helpers: `speckit-git-commit`,
`speckit-git-feature`, `speckit-git-initialize`, `speckit-git-remote`,
`speckit-git-validate`. Upstream adds and renames these between releases, so
treat the count as a sanity check against your pinned version rather than a
fixed contract.

---

## 13. `caveman` plugin (installed automatically by `install.sh`)

**Why this kit needs it:** Caveman is a Claude Code plugin that
switches the agent into a terse-output register, saving roughly 75%
of output tokens per upstream's measurement. The kit ships it as
`caveman@caveman` (marketplace: `JuliusBrussee/caveman`); `install.sh`
registers the marketplace and enables the plugin alongside the other
20 plugins.

**Version requirement:** The kit pulls whatever the
`JuliusBrussee/caveman` marketplace currently publishes. Re-run
`install.sh` to pick up a newer version (or `claude plugin upgrade
caveman@caveman` directly).

**Install:** automatic via the kit's `install.sh`. No separate
manual step.

Manual equivalent (what `install.sh` runs for you):
```sh
claude plugin marketplace add JuliusBrussee/caveman
claude plugin install caveman@caveman
```

Upstream's unified one-liner (only if you want extras like the
caveman-shrink MCP middleware or statusline badge that the kit's
plugin install doesn't include):
```sh
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

**Verification:**

```sh
claude plugin list | grep caveman   # should show caveman@caveman enabled
```

After Claude Code restart, the plugin's slash command (see upstream
docs for the current command name and the four mode flags: `lite`,
`full`, `ultra`, `wenyan`) appears in the palette. See
[`docs/tools/caveman.md`](tools/caveman.md) for when to invoke it and
when NOT to (it conflicts with `explanatory-output-style`).

---

## 14. `shellcheck` (kit-development only)

**Why this kit needs it:** `shellcheck` is used to lint `install.sh`,
`uninstall.sh`, and `scripts/*.sh` during development of the kit itself.
It is not required at runtime for users of the kit — only for
contributors editing the shell sources.

**Version requirement:** `shellcheck >= 0.8`. Earlier versions miss
checks the kit's shell scripts rely on.

**macOS:**

```sh
brew install shellcheck
```

**Linux (Debian/Ubuntu):**

```sh
sudo apt install -y shellcheck
```

**Linux (Fedora/RHEL):** `sudo dnf install -y ShellCheck`

**Verification:** `shellcheck --version`. Run against the kit's shell
sources with `shellcheck install.sh uninstall.sh scripts/*.sh`.

---

## Sanity check

After installing the prerequisites you need, run this one-liner and
confirm every line prints a version (or, for `gh`, auth status):

```sh
claude --version && git --version && gh auth status && \
python3 --version && uv --version && node --version && npx --version && \
rg --version | head -1 && jq --version && gopls version && \
java -version && \
typescript-language-server --version && \
ls "$(npm root -g)/typescript/lib/tsserver.js" && \
shellcheck --version | head -2
```

Any failing line is a prerequisite to install before running `install.sh`.

`install.sh` itself does not install prerequisites; it assumes they are
present on the `PATH` it inherits.

### Getting the PATH to stick

Four of the installs above are keg-only, user-local, or otherwise not on
`PATH` by default. Collected in one place, macOS with Homebrew:

```sh
eval "$(/opt/homebrew/bin/brew shellenv)"                      # gh, uv/uvx, node/npx
export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"  # python3 >= 3.11  (§4)
export PATH="$HOME/go/bin:$PATH"                               # gopls            (§7)
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"              # java, for jdtls  (§9)
```

**Put these in the profile your shell actually reads**, which is not always
the one the tool's own installer suggests:

| Your shell starts as | Reads |
|---|---|
| A login shell (`-zsh` — Terminal.app, iTerm2 by default) | `~/.zprofile`, then `~/.zshrc` |
| An interactive non-login shell (many IDE terminals, `zsh` without `-l`) | `~/.zshrc` only |
| Any zsh at all | `~/.zshenv` |

`~/.zshenv` is the safe choice if you are unsure. Check with:

```sh
zsh -ic 'command -v node npx uvx python3 java gopls'
```

### Then start a new terminal, not just a new `claude`

This is the step that costs people the most time, so it is worth being blunt
about: **restarting `claude` inside an existing terminal does not pick up a
profile change.** `claude` inherits the environment of the shell process that
launched it, and that process was started before you edited anything. Claude
Code's MCP servers and plugin hooks then inherit *its* environment in turn —
they never read your profile themselves.

The symptom is a set of failures that all look unrelated: `node: command not
found` on every prompt, three MCP servers `✘ failed`, a plugin reporting the
wrong Python. One cause.

To tell whether this is what you are looking at, compare when your shell
started against when you edited the profile:

```sh
ps -o pid=,lstart=,comm= -p "$PPID"    # when this shell started
stat -f '%Sm %N' ~/.zshrc ~/.zprofile  # when the profile last changed
```

If the shell is older than the file, no restart of `claude` alone will ever
help — close the terminal window and open a new one.

`install.sh` also records the resolved PATH into `~/.claude/settings.json`'s
`env` block, which is what makes hooks and MCP servers independent of all of
this on subsequent sessions. That value is written from the directories
preflight verified, so it is a superset of a PATH already known to work; your
own `PATH` entry, if you have set one, is never overwritten.

### Installing prerequisites and running `install.sh` in separate shells

A `curl ... | sh` installer that writes into `~/.local/bin` (or `~/.cargo/bin`)
exports `PATH` for **its own process only**. Nothing persists that change, so a
later, separate `./install.sh` invocation searches the PATH it inherited and
reports the tool missing even though it is sitting on disk:

```
[cck] missing prerequisite: claude
```

This bites on an already-running machine rather than a fresh throwaway build
box, because on a build box the two steps usually share one shell. Either
re-export in the shell you are about to run the installer from:

```sh
export PATH="$HOME/.local/bin:$PATH"
./install.sh
```

or start a new login shell so your profile puts the directory on `PATH`, then
re-run. Preflight now checks the usual install directories and, when it finds
the tool in one of them, prints the path and the `export` line rather than only
reporting it missing. `hash -r` does not help here: a fresh `bash install.sh`
starts with an empty hash table, so the missing piece is the `PATH` entry
itself, not a stale lookup.

---

## Further reading

- [`docs/philosophy.md`](philosophy.md) — principles the kit enforces.
- [`docs/workflow.md`](workflow.md) — the 10-step development loop.
- [`docs/corporate-tls.md`](corporate-tls.md) — TLS-intercepting proxy
  configuration.
- [`docs/tools/`](tools/) — per-tool rationale documents.
