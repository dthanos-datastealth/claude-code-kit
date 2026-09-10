# claude-code-kit — install findings (prerelease @ 4d08e48)

Environment: macOS 26.6.2 arm64, Claude Code 2.1.267, fresh `~/.claude/`
(no CLAUDE.md, settings.json had only `theme`/`tui`), Homebrew present but
not on PATH, no gh/uv/node, system python3 = 3.9.6.

`install.sh` itself ran clean: 6/6 marketplaces, 22/22 plugins, no retries,
`theme`/`tui` preserved, `effortLevel: xhigh` added, no CLAUDE.md written.
Every finding below is in the **docs / post-install path**, not the installer
core — except #1, #9 and #10.

---

## 1. Preflight does not check the Python version — only presence

`install.sh:preflight()` calls `require python3`, which is
`command -v python3`. `pyproject.toml` declares `requires-python = ">=3.11"`
and `docs/prereqs.md` §4 says "Earlier versions miss type syntax used in the
lint scripts."

On this box `python3` was 3.9.6 and preflight passed. The settings merge
happens to survive 3.9 (`list[str]` annotations are PEP 585, valid since
3.9), so the failure would surface later and elsewhere, not at the gate.

Confirmed downstream: after install, the `security-guidance` plugin reported
its cross-file commit reviewer (layer 3 of 3 — IDOR, auth-bypass, cross-file
SSRF) as **unavailable** because "the hook is running on 3.9". A plugin the
kit ships was silently degraded by a prerequisite the kit declares but does
not enforce.

**Fix:** version-check in `require`, e.g.
`python3 -c 'import sys; raise SystemExit(sys.version_info < (3,11))'`,
with the same "found it at <dir>" treatment the PATH check already has.

## 2. `docs/prereqs.md` §10 registers the dual-graph MCP at the WRONG SCOPE

The documented recipe:

```sh
claude mcp add dual-graph "$GS" -- --stdio
```

wrote to `projects["/Users/bob/claude-code-kit"].mcpServers` in
`~/.claude.json` — **project-scoped to whatever directory you ran it in**.
The doc asserts the opposite: "`claude mcp add` writes to the per-`$HOME`
`.claude.json` `mcpServers` section."

This is the highest-impact finding. `20-kit-code-search.md` makes
`graph_continue` the mandatory FIRST call for every lookup in every project.
Following the doc verbatim gives you a dual-graph MCP that exists only in
the kit's own checkout; in every real project the first leg of the search
order silently no-ops and the kit falls back to exactly the grep it forbids.
`claude mcp list` run from the kit directory reports it connected, which
masks the miss — the same trap the doc's own "Per-HOME registration" note
warns about, one level up.

**Fix:** `claude mcp add --scope user dual-graph "$GS" -- --stdio`, and
correct the surrounding prose.

## 3. The PyPI `graperoot` path installs no `graperoot` launcher

`uv tool install --python 3.12 graperoot` installed 6 executables:
`context-packer`, `dg-graph`, `dgc-claude`, `graph-builder`,
`mcp-graph-server`, `mcp-graph-server-stdio`. There is no `graperoot`.

`docs/prereqs.md` §10 recommends this path ("Reproducible, no auto-updater —
what this kit recommends") and then tells the reader to opt out of telemetry
with `graperoot --no-telemetry` / `--no-auto-update` and to "confirm they
exist in `graperoot --help` on the version you installed." Neither the
command nor the check is reachable on the recommended path.

**Fix:** state that the opt-out flags belong to upstream's shell-installer
launcher only, and document what (if anything) suppresses telemetry on the
PyPI path — an env var, or nothing.

## 4. `mcp-graph-server --help` hangs the terminal

It does not handle `--help`; it starts the stdio server and blocks. Timed
out at 120s and had to be killed. Anyone following #3's "check
`--help`" advice on the PyPI binary hangs their shell.

**Fix:** note it, or point the check at `dg-graph`/`graph-builder`.

## 5. The documented jdtls verification cannot detect the failure it claims to

`docs/prereqs.md` §9 macOS recipe is `brew install openjdk@21 jdtls`; README
step 4c says Homebrew "pulls a current JDK as a dependency". It pulled
`openjdk 26.0.2.1` — but **Homebrew's openjdk is keg-only**, so it is not
symlinked onto PATH. After a successful install:

```
$ java -version
The operation couldn't be completed. Unable to locate a Java Runtime.
```

Both verification commands are wrong about this:

- prereqs.md §9: `java -version  # should print openjdk 21.x or newer` — fails.
- README: `jdtls --help  # JVM mismatch surfaces here if any` — **exited 0
  and printed usage on a box with no JVM at all.** `jdtls` is a Python
  launcher; `--help` never touches the JVM. The check is structurally
  incapable of catching the condition it exists to catch, which is precisely
  the failure mode `docs/verification-standards.md` is written against.

**Fix:** add the keg-only PATH line
(`export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"`) to §9, and replace the
`--help` check with one that actually starts the JVM.

## 6. README's LSP verification omits the `gopls` PATH requirement

README: `which gopls typescript-language-server jdtls  # all three resolve`.
`go install` puts `gopls` in `$(go env GOPATH)/bin` (`~/go/bin`), not on PATH
by default. prereqs.md §7 does say to add it; the README verification block
does not, so the reader hits a "MISSING" they were just told to expect to
resolve.

## 7. `docs/prereqs.md` §12 version string mismatch

Install pins `v0.8.16`; verification says `should print: specify 0.8.15`.
Actual output: `specify 0.8.16`. Cosmetic.

## 8. "Required setup after install.sh" omits three credential steps

The README table covers Berry, dual-graph and the three LSPs. It does not
mention that:

- `notion` is an HTTP MCP needing interactive OAuth via `/mcp`
  (plus the enterprise port-pinning caveat the kit itself ships a fix for).
- `huggingface-skills` is an HTTP MCP at `https://huggingface.co/mcp?login`
  — also interactive OAuth.
- `context7` reads `${CONTEXT7_API_KEY:-}`; it works anonymously but is
  rate-limited without one.

Three of the 22 plugins are therefore non-functional after following the
documented setup to completion.

## 9. Rule 20 names tools the harness can withdraw — and does

`20-kit-code-search.md` step 3 requires the `Grep`/`Glob`/`Read`/`Edit`
tools and step 4 declares bash `grep`/`find`/`cat`/`sed`/`awk`
"**FORBIDDEN. Never.**"

Under Claude Code's `auto` permission mode, `Grep` and `Glob` **do not
exist** — not as tools, not as deferred tools. `ToolSearch` for them returns
no match, and the harness error reads: *"Glob is not available in this
session — find files with `find` via the Bash tool instead."* Auto mode's
own instruction to the model is the exact inverse of rule 20:

> Do your work through the Bash tool wherever it can accomplish the job:
> read files with `cat`, `head`, or `sed -n`, search with `grep` and `find`
> … rather than using the dedicated Read, Edit, or Write tools.

So in auto mode rule 20 step 3 names two tools that are absent, and step 4
forbids the only remaining option. The rule's stated rationale — bash tools
"require permission, stall autonomous work" — is also inverted: auto mode
exists precisely so Bash does not prompt.

`auto` is one of six modes (`acceptEdits`, `auto`, `bypassPermissions`,
`manual`, `dontAsk`, `plan`, per `claude --help`). Nothing kit-side can
restore a tool the mode removed: rule files are prompt content, and tool
registration happens before the model is invoked.

**Fix (two parts):**
1. Rewrite steps 3–4 to name *capabilities* rather than tool
   implementations, and to degrade gracefully when the structured search
   tools are absent. Step 1 (`graph_continue` first) is portable and should
   carry the weight.
2. If the kit genuinely requires that tool surface, declare it:
   ship `"permissions": {"defaultMode": "acceptEdits"}` in
   `claude/settings.json` rather than assuming it. See #10.

## 10. `merge-policy.json` has no entry for `permissions`

`scripts/merge-policy.json` defines strategies for `env`, `enabledPlugins`,
`extraKnownMarketplaces` and `effortLevel`, with
`default_strategy_for_unlisted_keys: preserve_user`.

If the kit starts shipping `permissions` (per #9), the unlisted-key default
means the kit's value is **never applied on upgrade** — `preserve_user`
keeps whatever is already there and the kit's declaration is dropped
silently. The policy file's own comment anticipates this: "Kit never
introduces new top-level keys without adding them here first."

**Fix:** add a `permissions` policy entry before shipping the key. A nested
`union_dict` with `winner_on_conflict: user` on `permissions.allow` but
kit-wins on `defaultMode` is probably what is wanted, which the current
flat-key policy schema cannot express — the schema may need a nested form.

## 11. `berry-configure` omits the model pin the kit calls mandatory

The Berry plugin's own `commands/berry-configure.md`, Step 5, for "local
llama.cpp or other OpenAI-compatible endpoint" (the OpenRouter case):

> Write `~/.berry/mcp_env.json` with `OPENAI_API_KEY` and `OPENAI_BASE_URL`
> set to the user's values.

No `BERRY_VERIFIER_MODEL`, no `BERRY_VERIFIER_BACKEND`. The kit's
`50-kit-plugins.md` states the opposite as a hard requirement:

> **Always pin `BERRY_VERIFIER_MODEL`.** The fallback takes the first model
> from `GET /v1/models`, which on OpenRouter is arbitrary and probably lacks
> the token logprobs Berry requires.

So a user who follows the supported configure flow verbatim against
OpenRouter gets an unpinned verifier that resolves to an arbitrary model,
most of which lack logprobs. Berry then fails closed with
`{"flagged": true, ..., "error": ...}` — which reads like a failed claim
rather than a broken verifier, exactly the confusion `docs/tools/berry.md`
warns about.

Step 5's `config.json` template is also lossy: it writes `allow_web: false`
and omits `enforce_verification`, so applying it literally would silently
downgrade an existing config. The command's prose does say to merge rather
than replace, but the template shown contradicts it.

**Fix:** upstream the model pin into `berry-configure.md` Step 5 for the
OpenAI-compatible branch, or have the kit ship its own configure wrapper.
Until then the kit's rule and the plugin's command disagree, and the plugin
is the one users will follow.

## 12. Node is a hard runtime dependency of four enabled plugins, and is neither declared nor checked

`enabledPlugins` ships `caveman@caveman`, `playwright`,
`chrome-devtools-mcp` and `context7`. All four require `node`/`npx` at
runtime. None of the following mention Node as a prerequisite:

- README's prereq table — `claude`, `git`, `gh`, `python3`, `uv`. Five entries, no Node.
- `install.sh:preflight()` — requires those same five.
- `docs/prereqs.md` §13 (caveman) — install and verification steps, no Node.

Node appears only in §8, framed as a dependency of
`typescript-language-server`, which is an *optional* post-install step.

`prewarm_npx_mcps()` treats a missing `npx` as non-fatal: it warns and
continues. So on a machine without Node, `install.sh` completes
successfully and reports "Done", after which:

- caveman's `UserPromptSubmit` hook fails on **every prompt** with
  `/bin/sh: node: command not found`,
- three MCP servers fail to connect,
- and nothing in the install output predicted any of it.

Observed on this machine end to end.

**Fix:** either `require node` / `require npx` in preflight and add Node to
the prereq table, or make the Node-dependent plugins opt-in. A hook that
runs on every prompt is the worst place for an undeclared dependency —
it converts a missing optional tool into continuous, unavoidable noise.

## 13. `brew install python@3.12` does not put `python3` on PATH

`docs/prereqs.md` §4, macOS:

```sh
brew install python@3.12
```

> Homebrew's `python@3.12` formula installs Python 3.12, which satisfies
> the `>= 3.11` constraint.
>
> **Verification:** `python3 --version` (expect 3.11+).

The formula is keg-only for the unversioned names. Homebrew's own caveats,
printed during this install:

> Unversioned and major-versioned symlinks `python`, `python3`,
> `python-config`, `pip`, `pip3`, etc. … are installed into
> `/opt/homebrew/opt/python@3.12/libexec/bin`

Observed immediately after a successful install:

```
python3      /usr/bin/python3        Python 3.9.6
python3.12   /opt/homebrew/bin/python3.12   Python 3.12.14
```

The documented verification therefore **fails on a correctly followed
install**, and everything that shells out to `python3` — `install.sh`'s
merge step, the lint scripts, and the `security-guidance` hook — keeps
using the system 3.9. This is the upstream cause of the degraded
`security-guidance` reviewer recorded in #1.

**Fix:** either add the PATH line
(`export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"`) to §4, or
recommend `brew install python3`, which does link the unversioned name.
Same class as #5 — a keg-only Homebrew formula documented as if it were
linked.

### The consolidated PATH the kit never gives you

Findings #5, #6 and #13 are three instances of one gap: the kit's
prerequisites are spread across sections that each install a tool, and no
section states the resulting PATH as a whole. A working macOS/Homebrew
install needs all four lines, and the reader has to assemble them:

```sh
eval "$(/opt/homebrew/bin/brew shellenv)"                        # gh, uv, node/npx
export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"    # python3 >= 3.11  (#13)
export PATH="$HOME/go/bin:$PATH"                                 # gopls            (#6)
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"                # java for jdtls   (#5)
```

**Fix:** add this block to `docs/prereqs.md`, next to the "Sanity check"
one-liner, with the note that Claude Code must be launched from a shell
that has sourced it.

## 14. Ship PATH in `settings.json` `env` — verified, and the recommended fix

Previously logged as an unverified candidate; now confirmed against the
docs and applied on this machine. **This is the fix that makes findings
#5, #6, #12 and #13 stop mattering**, because it removes the kit's
dependence on shell configuration entirely.

Claude Code's env-vars documentation:

> Claude Code writes each `env` entry into the process environment,
> **replacing the value inherited from the shell.**

Two consequences that dictate how it must be written:

1. **No variable expansion.** `"${PATH}"` or `"$PATH"` are not expanded.
   The value has to be a complete absolute PATH.
2. **It replaces, not extends.** A value omitting `/usr/bin` and `/bin`
   would be far worse than the problem it solves. Every system directory
   must be listed explicitly.

Applied here, and every required tool resolves within it:

```json
"env": {
  "UV_NATIVE_TLS": "1",
  "PATH": "$HOME/.local/bin:/opt/homebrew/opt/openjdk/bin:$HOME/go/bin:/opt/homebrew/opt/python@3.12/libexec/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}
```

(`$HOME` shown for readability only — the real value must be literal
absolute paths, and the machine-specific entries mean the kit cannot ship
this verbatim.)

**The design problem for the kit:** PATH is machine-specific — Homebrew
prefix differs on Intel macOS (`/usr/local`) versus Apple Silicon
(`/opt/homebrew`), `GOPATH` varies, the Python formula version varies, and
Linux differs again. So the kit cannot hardcode it in
`claude/settings.json`. The realistic options:

- Have `install.sh` **compute** the PATH at install time from the tools it
  just verified in preflight, and write it into the `env` block. Preflight
  already resolves each binary's location, so the data is in hand.
- Or ship a documented template in `docs/prereqs.md` with the four
  machine-specific slots called out for the user to fill.

The first is strictly better: it makes the thing the kit already checks
(preflight) produce the thing the kit needs (a correct runtime PATH),
instead of checking it and then discarding the result.

**Note also #10 applies:** `merge-policy.json` gives `env` a
`union_dict`/`winner_on_conflict: user` strategy, so a kit-computed `PATH`
would never overwrite a user's existing one on upgrade. That is probably
correct, but it means a stale user PATH survives forever — worth an
explicit decision rather than an accident.

**Observed discrepancy, not a kit issue:** the same docs state that "a
running session applies new and changed values to its environment when you
save the file." Saving a `PATH` entry into `env` did **not** change what
tool subprocesses in the already-running session resolved — they still saw
the old inherited PATH. A restart was still required. Worth knowing before
relying on the live-apply behaviour.

---

# Findings from the full test pass

Environment at test time: all prerequisites resolving, 22/22 plugins
enabled, all MCP servers healthy per `claude mcp list`, kit test suite
174 passed / 1 skipped, all five lint scripts exit 0.

## 15. `upgrade.sh --status` never reports drift, though it claims to

`scripts/upgrade.sh` line 8 documents the flag as "Report current install
state + **drift** + unresolved conflicts", and
`plugins/claude-code-kit/skills/status/SKILL.md` promises:

> Whether live `CLAUDE.md` and `settings.json` SHA matches the recorded SHA
> (drift detection — user has manually edited a kit-owned file)

Measured with a genuinely drifted `settings.json`:

```
recorded: 7b41ffefbb34e7dba9d2863d9cbdf7b37fbcdf99c3d34e05463f11fc6fd34e22
actual:   2767f7719a29dddd14872b304bc6550419ae4ecc521c7696b0199e092e3b8ec2
DRIFTED
```

`--status` output: version block, "Unresolved conflicts: (none)", "Backups
available". No drift line at all. `grep -i 'drift\|sha' scripts/upgrade.sh`
matches only comments — the comparison is never performed.

A status command that reports health it did not check is the same defect
class `docs/verification-standards.md` is written against.

**Fix:** implement the SHA comparison, or delete the claim from both the
script header and the skill description.

## 16. `diff-settings.py` mislabels kit env keys as user-added, and ignores env in its exit code

`scripts/diff-settings.py:21,28`:

```python
le = set((live.get("env") or {}).keys())
...
"env_keys_only_in_live": sorted(le),
```

The kit's env keys are never subtracted, so the field reports *every* live
env key. On a stock install it always lists `UV_NATIVE_TLS`, which the kit
itself ships. Observed output on this machine:

```json
"env_keys_only_in_live": ["PATH", "UV_NATIVE_TLS"]
```

Only `PATH` is user-added. Should be
`le - set((kit.get("env") or {}).keys())`.

Second defect, same file, line 30: `has_delta` covers only plugins and
marketplaces. Env differences never affect the exit code, contradicting the
README's "Exits 0 when nothing has drifted, 1 when something has."

## 17. `UV_NATIVE_TLS` is deprecated by uv and slated for removal

Emitted by `uv` on every invocation during testing:

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be
removed in a future release. Use `UV_SYSTEM_CERTS` instead.
```

`UV_NATIVE_TLS=1` is the kit's **only** shipped env default and the entire
mechanism behind `docs/corporate-tls.md` §0 ("What the kit ships by
default"). When uv removes it, every corporate-TLS install silently loses
its fix and Berry's MCP server starts failing behind intercepting proxies
again — the exact symptom the doc was written to prevent.

**Fix:** ship `UV_SYSTEM_CERTS` (keeping `UV_NATIVE_TLS` for older uv if
both are tolerated), and update `docs/corporate-tls.md` and the README's
"Corporate TLS handling" section.

## 18. The documented TypeScript LSP install produces a non-functional LSP

`docs/prereqs.md` §8 and README step 4b both say:

```sh
npm install -g typescript typescript-language-server
```

`typescript` now resolves to 7.x, the native port, which ships **no
`tsserver.js`**:

```
$ ls $(npm root -g)/typescript/lib/
getExePath.d.ts  getExePath.js  tsc.js  version.cjs  version.d.cts
$ python3 -c "...package.json..."
version: 7.0.2
bin: {'tsc': './bin/tsc'}
```

`typescript-language-server` requires `tsserver.js`. Result, on a correctly
followed install:

```
Error performing documentSymbol: Request initialize failed with message:
Could not find a valid TypeScript installation. Please ensure that the
"typescript" dependency is installed in the workspace or that a valid
`tsserver.path` is specified. Exiting.
```

Verified in both directions. After `npm install -g typescript@5`
(5.9.3, `lib/tsserver.js` present), the same LSP call succeeds:

```
Document symbols:
greet (Function) - Line 1
msg (Constant) - Line 5
```

Note this defeats the kit's own verification step: `tsc --version` prints
`7.0.2` and `which typescript-language-server` resolves, so both documented
checks pass while the LSP is dead. Same structural problem as #5.

**Fix:** pin the major version — `npm install -g typescript@5
typescript-language-server` — and replace the `tsc --version` check with
one that asserts `tsserver.js` exists, or that actually starts the server.

gopls and jdtls were tested the same way and both work: gopls returned
correct `documentSymbol` and `findReferences`; jdtls resolved
`Main`/`greet`/`main` against openjdk 26.0.2.1.

## 19. Rule 50's `audit_trace_budget` example omits `cites`, producing a silent no-op gate

`50-kit-plugins.md` documents the call as:

```python
spans=[{"sid": "S0", "text": "actual test output content here"}]
```

Executed verbatim against `berry@2.1.0-rc.1` (server version 1.30.0):

```
status: empty_context
verifier_calls: 0
reasons: ['selected context is empty for this claim']
flagged: true
```

The verifier is **never called**. `audit_trace_budget` defaults to
`context_mode: "cited"`, which selects only spans a step explicitly cites,
and the documented example has no `cites` field. The result is
`flagged: true` — indistinguishable from a real evidence failure, and it
triggers the 3-strike rule on a claim that was never actually verified.

Adding `cites` fixes it. Same claim, same span:

| Call | status | verifier_calls |
|---|---|---|
| `{"claim": C}` + spans (as documented) | `empty_context` | 0 |
| `{"claim": C, "cites": ["S0"]}` + spans | `not_entailed` / `passed` | 1 |
| `{"claim": C}` + spans + `context_mode: "all"` | `not_entailed` | 1 |

**Fix:** rule 50's example must include `cites`, or set
`context_mode: "all"`. As written it documents a call that silently
verifies nothing — the worst possible failure for the kit's central gate.

## 20. Rule 50's and philosophy.md's account of the failure mode is out of date

Two related inaccuracies against `berry@2.1.0-rc.1`.

**a) The wrong-span-shape symptom.** Rule 50 says the malformed shape
`{"<id>": "<content>"}` "silently produces 0 observed bits every time", and
`docs/philosophy.md` §5 elaborates on the KL divergence collapsing.
Measured, the malformed shape is now caught explicitly:

```
status: no_spans
verifier_calls: 0
reasons: ['no spans were provided, so the claim cannot be verified']
```

Not silent, and not zero-bits. The documented debugging advice ("When you
see 0 or near-0 bits on a span you believe is genuine, check the key names
first") no longer matches any output the tool produces.

**b) `observed_bits` is not in the output.** The field appears nowhere in
`audit_trace_budget`'s response in this version. Every result reports
posterior YES bounds against a target instead:

```
reasons: ['posterior_below_target',
          'posterior YES lower bound 0.892237 is below target 0.95']
```

`50-kit-plugins.md`, `docs/philosophy.md` §5 and `docs/workflow.md` step 2
all explain the gate in terms of `observed_bits` and "insufficient bits".
A user debugging a flagged claim will look for a field that does not exist.

**Fix:** re-document the gate in terms of posterior bounds vs `target`, and
replace the zero-bits troubleshooting with the actual `status` taxonomy
(`passed`, `not_entailed`, `contradicted`, `empty_context`, `no_spans`).

**Verified working, for the record:** the gate itself is sound. With cited
spans it calls the verifier, and it discriminates correctly — a supported
claim scored posterior 0.892 (`not_entailed` at target 0.95, `passed` at
0.85), an unsupported claim scored 0 (`contradicted`), and a tightly-worded
true claim `passed` at the default 0.95. A claim asserting more than its
span supports is correctly flagged. Backend `openai`, model
`openai/gpt-4o-mini`, all three OpenRouter endpoints expose `logprobs` and
`top_logprobs`.

## 21. Dual-graph returns tests-only at `confidence: high`, and rule 20 forbids looking further

`graph_scan` on this repo: 106 files, 55 symbols, 689 edges. A natural
question — the way rule 20 says to open every lookup — returned:

```
query: "where is the settings.json merge policy applied and which function
        performs the union merge"
confidence: high
max_supplementary_greps: 0
max_supplementary_files: 0
recommended_files: tests/test_intelligent_settings_merge.py
                   tests/test_lint_merge_policy.py
                   tests/test_install_merge_settings.py
```

All three are tests. The implementation,
`scripts/intelligent-settings-merge.py`, is absent. Rule 20 says `high`
means "stop, do not grep or explore further", and the supplementary budget
is zero — so an agent obeying the rule answers from tests and never reaches
the code.

Re-querying with the filename already in it surfaces the implementation
first. That is the opposite of the tool's purpose: it works once you know
where to look.

One repo, largely shell and Markdown, 55 indexed symbols — so this is not a
general claim about the engine. But it is the kit's own repo, and it is the
first thing a new user will point the graph at.

**Fix:** rule 20 should not treat `confidence: high` as a hard stop when
`recommended_files` contains only test files. A cheap heuristic — if every
recommendation is a test, spend the supplementary budget — would prevent
the failure mode.

## 22. A resumed session keeps stale MCP failures while the CLI reports healthy

After the PATH fix, `claude mcp list` reports:

```
plugin:berry:berry: ... - ✔ Connected
plugin:playwright:playwright: ... - ✔ Connected
plugin:chrome-devtools-mcp:chrome-devtools: ... - ✔ Connected
```

The same session simultaneously refuses those tools:

```
plugin:berry:berry: "Skipping connection (recent failure cached retries
automatically in 15 min, or edit the plugin config to retry now)"
```

`claude mcp list` spawns a fresh process and succeeds; the resumed session
carries the cached failure from before the fix. The two disagree, and the
CLI is the one users will trust. Berry could not be tested through its MCP
tools at all — the gate had to be driven directly over stdio.

Not a kit bug, but the kit depends on Berry being reachable and should say:
after fixing PATH, start a **fresh** session, not a resumed one, and treat
`claude mcp list` as unreliable evidence about the current session.

## 23. The caveman statusline command pins a plugin version hash

Offered by the caveman plugin and added during setup:

```json
"statusLine": {
  "type": "command",
  "command": "bash \"/Users/bob/.claude/plugins/cache/caveman/caveman/15581d14007f/src/hooks/caveman-statusline.sh\""
}
```

The path contains the plugin version `15581d14007f`. A plugin upgrade
writes a new directory and the statusline breaks silently — a `statusLine`
whose command exits non-zero simply shows nothing.

If the kit adopts this, it needs a version-independent wrapper or a
post-upgrade repair step. Related to #10: `statusLine` is also absent from
`merge-policy.json`.

---

# Findings from the upgrade / rollback / uninstall pass

All run against isolated `$HOME`s. Real `~/.claude/settings.json` sha
verified unchanged before and after every test.

**What passed:** `test-upgrade-isolated.sh` (all 4 user mutations preserved,
leak check clean); a full backup-then-rollback cycle (marker restored
correctly); rollback's error handling for a missing and a bogus backup id;
`uninstall.sh`'s rule-file selectivity (removed the 6 kit rules, kept
`00-user-overrides.md` and a hand-added `99-my-own.md`);
`fix-notion-mcp-port.sh` port validation and `callbackPort` write.

## 24. `test-install-isolated.sh` always fails, and its leak check never runs

Line 87:

```bash
for f in CLAUDE.md settings.json memory/MEMORY.md; do
```

exits 1 at line 92 when a file is missing. On Claude Code >= 2.0.64 the kit
**deliberately does not write `CLAUDE.md`** — `install.sh:copy_templates()`
returns early on `kit_rules_supported`. So the assertion can never pass on a
current CLI. Observed:

```
[cck-test] Verifying isolated-HOME contents...
[cck-test]   CLAUDE.md MISSING
```

The install itself was correct — the isolated HOME contained `rules/` with
all 7 files, 22 plugins and 24 tool docs. Only the assertion is stale.

Three consequences, in increasing severity:

1. The hardcoded-path lint (line 112) never runs.
2. The skill-layout lint (line 125) never runs.
3. **The leak check (line 133) never runs** — the assertion that the real
   `~/.claude/` was untouched, which is the entire stated purpose of the
   harness. The README devotes a section to it: "then *proves* your real
   `~/.claude/` is untouched by comparing mtimes". It proves nothing,
   because it exits four steps earlier.

I verified by hand that no leak occurred, but the harness did not.

Also: the early exit skips the `--clean` branch, so every run abandons its
isolated HOME. Measured: **961 MB** per invocation.

**Fix:** assert on `rules/` when `kit_rules_supported`, `CLAUDE.md` only
below the floor. Add a `trap` so the tempdir is cleaned on failure too.

This is the same root cause as #26: the rules migration updated
`install.sh` but not the things that check it.

## 25. `upgrade.sh --dry-run` produces no diff

README: `bash scripts/upgrade.sh --dry-run # preview the diff`.
`skills/upgrade/SKILL.md` step 2: "Surfaces the diff in chat, including:
settings.json key changes (new plugins added, existing plugins preserved,
env vars merged) / CLAUDE.md section changes".

Actual output against a real, drifted install:

```
[cck-upgrade] Mode: dry-run
[cck-upgrade] (dry-run: would move any kit sections out of CLAUDE.md into rules/)
[cck-upgrade] settings.json merge...
  (dry-run: settings.json not written)
[cck-upgrade] (dry-run: would refresh .../docs/ and .../rules/)
[cck-upgrade] (dry-run: no files written)
```

Nothing written — correct. But no diff, so the confirmation gate the skill
describes (`[y]` proceed / `[n]` abort / `[c]` CLAUDE.md only / `[s]`
settings only) asks the user to approve a change they cannot see.

`scripts/diff-settings.py` already computes a structural delta. Wiring it
into the dry-run path would close this.

## 26. Backups omit `rules/`, so the kit's own instructions cannot be rolled back

`scripts/_kit_backup.sh:kit_backup_files()`:

```bash
for f in CLAUDE.md settings.json; do
```

Since the kit moved its instructions out of `CLAUDE.md` and into
`~/.claude/rules/`, the backup set no longer contains the kit's actual
instruction content. `kit_copy_rules` replaces all six kit rule files
wholesale on every upgrade.

Net effect: an upgrade that ships a bad rule cannot be reverted by
`/claude-code-kit:rollback` or by `uninstall.sh`. Both restore
`settings.json` and a `CLAUDE.md` that is no longer written, and leave the
new rule files in place. Verified: after rollback, `settings.json`'s marker
reverted correctly while `rules/` stayed at the upgraded content.

`docs/upgrading.md` presents rollback as one of "three layers of revert".
For the instruction layer there are zero.

**Fix:** add `rules/` to `kit_backup_files`, and restore it in both the
rollback path and `uninstall.sh`.

## 27. `uninstall.sh` leaves settings.json fully kit-configured on a clean-machine install

`kit_backup_files` only backs up files that already exist. On a clean
machine `install.sh` therefore creates **no backup at all** — confirmed,
`backups/` was empty after a fresh isolated install.

`uninstall.sh` handles that case ("No backup to restore from; removing what
the kit installed") and removes `rules/`, `docs/` and the state files. But
it never touches `settings.json`, so after "uninstalling" the machine still
has all 22 `enabledPlugins`, all 6 `extraKnownMarketplaces`,
`effortLevel: xhigh` and the kit's `env` block — permanently.

README: "Restores `~/.claude/CLAUDE.md` and `~/.claude/settings.json` from
the most recent timestamped backup." `docs/upgrading.md`: "nuclear option
… Use to leave the kit completely." Neither holds for the most common
case, a first install on a clean machine.

**Fix:** either have `install.sh` snapshot `settings.json` even when
absent (recording "absent" so uninstall can delete it), or have
`uninstall.sh` subtract the kit's own keys when no backup exists.

## 28. `fix-notion-mcp-port.sh` registers project-scoped, not user-scoped

Same defect class as #2. The script runs:

```sh
claude mcp add --transport http --callback-port "$PORT" notion "$NOTION_MCP_URL"
```

with no `--scope user`. Observed:

```
Added HTTP MCP server notion with URL: https://mcp.notion.com/mcp to local config
File modified: .../.claude.json [project: /Users/bob/claude-code-kit]
```

Resulting config — user scope empty, entry under the project that happened
to be the working directory:

```json
"projects": {
  "/Users/bob/claude-code-kit": {
    "mcpServers": {
      "notion": {"type": "http", "url": "...", "oauth": {"callbackPort": 51234}}
    }
  }
}
```

The port pin therefore applies in exactly one directory. Everywhere else
Notion keeps picking a random callback port — the precise failure the
script exists to fix, and the user has no signal, because it works in the
directory they tested from.

Both docs assert the opposite. Script header: "Per-HOME: writes via
`claude mcp add` which targets the current HOME's ~/.claude.json".
`docs/notion-mcp-pinning.md`: "writes the config to the **per-HOME**
`~/.claude.json` (scoped to the current project path)" — internally
contradictory in one sentence.

**Fix:** add `--scope user`, and correct both documents. Worth auditing
every `claude mcp add` the kit emits; two of two found so far have this bug.

## 29. spec-kit's documented skill count is wrong, and inconsistent between docs

`docs/prereqs.md` §12:

> After init, `ls .claude/skills/ | grep speckit` should list nine
> directories (`speckit-constitution`, `speckit-specify`, `speckit-clarify`,
> `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-checklist`,
> `speckit-implement`, `speckit-taskstoissues`).

Actual, `specify-cli 0.8.16`, the version the kit pins: **14**. The nine
listed plus `speckit-git-commit`, `speckit-git-feature`,
`speckit-git-initialize`, `speckit-git-remote`, `speckit-git-validate`.

`docs/tools/spec-kit.md` says "ten core commands upstream" — a third
number. The kit states three different counts for the same install.

Minor but real: `specify init --here` prompts for confirmation in any
non-empty directory, which every real project is. The kit presents the
command as a one-liner without mentioning `--force`, so a scripted or
non-interactive run aborts:

```
Warning: Current directory is not empty (1 items)
Do you want to continue? [y/N]: Aborted.
```

## 31. `test-upgrade-isolated.sh` reports a false LEAK from inside a live session

Found while re-running the harnesses to verify the fixes for #24 — the
sibling harness has the bug that `test-install-isolated.sh` already fixed.

Its leak check keys `~/.claude.json` on **mtime**:

```sh
REAL_CLAUDE_DOTJSON_BEFORE=$(file_mtime "${HOME}/.claude.json")
```

`test-install-isolated.sh` digests the `mcpServers` key instead, and carries
a comment explaining exactly why: `~/.claude.json` also holds the CLI's own
session state — caches, counters, tips history, `pluginUsage` — which a
running Claude Code session rewrites every few seconds. Measured there: the
whole-file digest changes inside 70 seconds with no install running at all,
while `mcpServers` holds still.

So the upgrade harness fails for anyone who runs it from inside a live
session, which is everyone. Observed:

```
[cck-upgrade-test] Step 6: leak check — real ~/.claude/ must be untouched...
[cck-upgrade-test]   LEAK: ~/.claude.json mtime changed
```

Everything before it passed. The failure is entirely spurious, and it is the
worst kind of spurious: a leak warning is exactly the message a developer
must not learn to ignore.

It also exits without removing its isolated HOME — about 1 GB per failed
run, same as #24.

**Fix:** port `dotjson_mcp_servers()` from the sibling harness, and add the
same `EXIT` trap. Both applied; the harness now passes and leaves no
tempdir behind.

**The general point** is the one worth carrying: this is the third instance
of a fix landing in one of two parallel implementations. #24 (rules-aware
artifact assertions), #26 (backups covering `rules/`) and this one are all
"the sibling never got the update". Whenever these two harnesses diverge,
one of them is wrong.

---

## Not kit bugs, but worth a line in the docs

- **Homebrew installed but not on PATH** produced exactly the failure
  `docs/prereqs.md` describes in "Installing prerequisites and running
  install.sh in separate shells". Preflight's `find_off_path` covers
  `/opt/homebrew/bin`, so it would have caught `gh`/`uv` — good design,
  worked as intended.
- **MCP servers *and plugin hooks* inherit the launching process's PATH**,
  not the interactive shell's. Observed together in one session:

  | Symptom | Missing executable |
  |---|---|
  | `plugin:berry:berry (ENOENT)` | `uvx` |
  | `plugin:playwright`, `plugin:chrome-devtools` (ENOENT) | `npx` |
  | `UserPromptSubmit hook error: node: command not found` | caveman hook → `node` |
  | `security-guidance`: "hook is running on 3.9" | `python3` |

  **"Restart Claude Code" is not sufficient, and the reason is the shell
  process, not the shell type.** `install.sh` ends with "Restart Claude
  Code" and the README repeats it. Neither says that restarting `claude`
  inside an existing terminal changes nothing: `claude` inherits the
  environment of the shell process that launches it, and that process was
  started before the PATH was edited.

  Measured on this machine after a full quit-and-relaunch of `claude`:

  ```
  login shell pid 721 started   Thu 10 Sep 12:08:59
  ~/.zprofile edited            Thu 10 Sep 13:37:01
  ~/.zshrc   edited             Thu 10 Sep 13:46:38

  PATH: /Users/bob/.local/bin:/usr/local/bin:/usr/bin:/bin:...
  node MISSING   npx MISSING   uvx MISSING   gh MISSING   python3 -> 3.9.6
  ```

  The launching shell had been alive for ~90 minutes before either edit.
  No profile change can reach it. Editing a *different* profile file does
  not help either, and chasing that is the trap: the shell here is `-zsh`
  (leading dash = **login** shell), so `~/.zprofile` was the correct file
  all along — it had simply not been read since before the edit. This cost
  three restart cycles, two of them spent on a wrong "interactive
  non-login shell" hypothesis that the process table would have refuted
  immediately.

  **The diagnostic that actually settles it** — compare the launching
  shell's start time against the profile's mtime:

  ```sh
  # walk up from a shell inside Claude Code to find the launching shell
  ps -o pid=,ppid=,comm= -p $$
  ps -o pid=,lstart=,comm= -p <that shell's pid>
  stat -f '%Sm %N' ~/.zprofile ~/.zshrc
  ```

  If the shell predates the file, no restart of `claude` alone will ever
  work — the terminal session itself has to be replaced, or the PATH has
  to come from somewhere other than a shell.

  **Fix:** stop depending on shell configuration. See #14 — carry the PATH
  in `settings.json`'s `env` block, which Claude Code reads at startup and
  applies to its own process, so hooks and MCP servers inherit it no matter
  which shell (or how stale a shell) launched it. Secondarily, replace
  "Restart Claude Code" with "quit `claude` **and** start a new terminal
  session", plus the check `zsh -ic 'command -v node npx uvx'`.

  A second-order effect worth documenting: once an MCP server has failed
  this way, Claude Code caches it —
  `Skipping connection (recent failure cached retries automatically in
  15 min, or edit the plugin config to retry now)` — so the restart that
  finally fixes the PATH may still show the servers as down.

  The caveman case is the instructive one: its hook is declared in
  `.claude-plugin/plugin.json` as `node "$HOOK_ROOT/src/hooks/…js"` and runs
  under `/bin/sh`, so it fails on **every prompt** until Claude Code's
  process has the prereqs on PATH. It is the most visible symptom of the
  whole class, and the reason #12 (undeclared Node dependency) and #14
  (PATH in `env`) are the two highest-value fixes in this document.
