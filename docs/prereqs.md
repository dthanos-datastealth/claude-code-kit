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
```

Homebrew's `python@3.12` formula installs Python 3.12, which satisfies
the `>= 3.11` constraint. `python@3.11` is also acceptable.

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

**Verification:** `python3 --version` (expect 3.11+).

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

Ensure `$(go env GOPATH)/bin` is on your `PATH` so the installed `gopls`
binary is reachable.

**Verification:** `gopls version` and `which gopls`. See
[`docs/tools/lsp-gopls.md`](tools/lsp-gopls.md) for the rationale.

---

## 8. `typescript-language-server` and `typescript`

**Why this kit needs it:** Same rationale as `gopls`, but for TypeScript
and JavaScript. The LSP backs the same set of structured queries for
`.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, and `.mjs` files.

**Version requirement:** Current stable releases of both
`typescript-language-server` and `typescript`. The npm distribution
defaults are fine.

**Install (all platforms with Node.js installed):**

```sh
npm install -g typescript-language-server typescript
```

This requires `node` and `npm` on the `PATH`. If Node is not installed:

- **macOS:** `brew install node`
- **Linux (Debian/Ubuntu):** `sudo apt install -y nodejs npm` (or use
  [nvm](https://github.com/nvm-sh/nvm) for a recent Node release).
- **Linux (Fedora/RHEL):** `sudo dnf install -y nodejs npm`

**Verification:** `typescript-language-server --version` and
`tsc --version`. See [`docs/tools/lsp-typescript.md`](tools/lsp-typescript.md)
for the rationale.

---

## 9. Dual-graph MCP server (external prerequisite)

**Why this kit needs it:** The kit's mandatory code-navigation order is
dual-graph first, LSP second, grep last. The dual-graph MCP server is
what makes the first leg of that order possible; without it,
`graph_continue` returns nothing and the discipline collapses to
LSP+grep.

**Version requirement:** Whatever the upstream project publishes as
current.

**Install:** This kit does not bundle the dual-graph MCP. Follow the
upstream project's setup instructions, then run `claude mcp add` to
register it locally for your installation. The kit's `install.sh` does
not attempt to install it on your behalf because the upstream
distribution model is project-specific.

See [`docs/tools/dual-graph-mcp.md`](tools/dual-graph-mcp.md) for the
rationale and the MCP tools the kit's `CLAUDE.md` rules reference.

**Verification (after registering with `claude mcp add`):**

```sh
claude mcp list
```

Expect the dual-graph entry to appear in the list with status `ready` (or
the equivalent label your `claude` version uses for healthy MCP
connections).

---

## 10. Berry verifier LLM backend

**Why this kit needs it:** Berry's `audit_trace_budget` and
`detect_hallucination` tools call an OpenAI-compatible LLM backend to
compute the information-theoretic contribution of each evidence span to
each claim. Without a reachable backend, every Berry-gated step fails
because the verifier cannot score the spans.

**Version requirement:** Any OpenAI-compatible HTTP endpoint. The most
common configuration is a local `llama-server` from `llama.cpp` exposing
a chat-completions endpoint, but any compatible service works.

**Install:** See [`docs/tools/berry.md`](tools/berry.md) for the
configuration options the kit supports, the environment variables Berry
reads to discover the backend, and the autostart patterns
(launchd / systemd) for keeping the backend reachable across reboots.

**Verification:**

The Berry plugin exposes a configuration skill — invoke
`berry:berry-configure` after install and follow its prompts. The skill
probes the configured backend and reports whether it can reach it.

For a manual check against a local `llama-server` on port 8080:

```sh
curl -s http://127.0.0.1:8080/v1/models | jq .
```

A successful response lists the loaded model; an empty or error response
indicates the backend is not running or not reachable.

---

## 11. `shellcheck` (kit-development only)

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
python3 --version && uv --version && rg --version | head -1 && \
jq --version && gopls version && \
typescript-language-server --version && tsc --version && \
shellcheck --version | head -2
```

Any failing line is a prerequisite to install before running `install.sh`.

`install.sh` itself does not install prerequisites; it assumes they are
present on the `PATH` and fails silently at use-time if they are not.

---

## Further reading

- [`docs/philosophy.md`](philosophy.md) — principles the kit enforces.
- [`docs/workflow.md`](workflow.md) — the 10-step development loop.
- [`docs/corporate-tls.md`](corporate-tls.md) — TLS-intercepting proxy
  configuration.
- [`docs/tools/`](tools/) — per-tool rationale documents.
