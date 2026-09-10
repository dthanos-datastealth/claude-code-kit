#!/usr/bin/env bash
# Runtime-environment install. Sourced by install.sh AND scripts/upgrade.sh.
#
# Claude Code applies `settings.json`'s `env` block to its own process, and
# MCP servers and plugin hooks inherit that process's environment. They do NOT
# read the user's shell profile. So a prerequisite can be installed, exported,
# and verified by hand, and still be invisible to the caveman hook or Berry's
# uvx launcher — the only thing that matters is the environment `claude`
# itself was started with.
#
# Carrying PATH here removes the dependency on which shell started the
# session, and on how long ago that shell was started. The value is composed
# from the directories preflight just resolved plus the PATH the install ran
# under, so it is a superset of something already known to work; it is never
# a hand-written list. That matters because `env` REPLACES the inherited
# variable rather than extending it (no ${PATH} expansion is performed), so a
# value missing /usr/bin would break every session.
#
# Requires the caller to have defined CLAUDE_HOME and log().

# Tools whose directories must be reachable at runtime, not just at install
# time. This is also the list install.sh's preflight requires — the two are
# the same set by definition, so it is declared once here.
#
# node and npx are in it because four enabled plugins shell out to them, and
# one of those does it on every prompt: caveman registers a UserPromptSubmit
# hook that runs `node`, so a machine without it prints an error before every
# single turn. playwright, chrome-devtools and context7 launch through npx.
KIT_RUNTIME_TOOLS=(claude git gh python3 uv node npx)

# Env keys the kit writes into settings.json after the merge, as opposed to
# shipping them in claude/settings.json. They are machine-specific, so they
# cannot live in the template — but three other places need to know what they
# are: diff-settings.py must not report them as user additions, uninstall.sh
# must remove them, and the writer below must set them. The list lived in all
# four independently until a fifth key would have gone unnoticed by three of
# them. scripts/kit-runtime-env-keys.txt is the single source; the two Python
# scripts read the same file.
KIT_RUNTIME_ENV_KEYS_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/kit-runtime-env-keys.txt"

# Echo the PATH to persist: the inherited PATH first and unchanged, then the
# directories the prerequisites resolved from, then a floor of /usr/bin:/bin.
# First occurrence wins; empty entries are dropped.
#
# ORDER MATTERS, and getting it backwards is not a cosmetic bug. An earlier
# version PREPENDED the resolved directories. On a stock macOS box `git` is
# /usr/bin/git, so that hoisted /usr/bin to the front — ahead of the
# python@3.12 libexec directory docs/prereqs.md tells every reader to put
# first — and the composed PATH resolved python3 to the system 3.9. Written
# into settings.json, that is permanent, and it silently reintroduces the
# degraded security-guidance reviewer. The user's order is the user's.
#
# Appending the resolved directories therefore costs nothing and cannot
# reorder anything: `command -v` only finds what is already on PATH, so every
# directory it yields is already present and is skipped by the dedupe. They
# are appended anyway as a cheap belt-and-braces for a future caller that
# resolves a tool some other way.
#
# Pure shell on purpose. This function has to work when PATH is impoverished,
# which is exactly the situation it exists to repair; an earlier version
# forked `dirname` and `python3` and died with "command not found" when asked
# to compute a PATH that lacked them.
kit_compute_path() {
    local combined="${PATH}" tool resolved dir
    for tool in "${KIT_RUNTIME_TOOLS[@]}"; do
        if resolved="$(command -v "${tool}" 2>/dev/null)"; then
            # Only absolute/relative paths carry a directory; a shell builtin
            # resolves to a bare word and has none.
            case "${resolved}" in
                */*) dir="${resolved%/*}" ;;
                *)   continue ;;
            esac
            combined="${combined}:${dir}"
        fi
    done
    # `env` REPLACES the inherited variable rather than extending it, so a
    # composed PATH without these leaves the session unable to run anything.
    combined="${combined}:/usr/bin:/bin"

    local out="" part
    local IFS=:
    for part in ${combined}; do
        [ -n "${part}" ] || continue
        case ":${out}:" in
            *":${part}:"*) continue ;;   # already present, keep first position
        esac
        out="${out:+${out}:}${part}"
    done
    printf '%s' "${out}"
}

# Write env keys the kit needs at runtime into settings.json, without
# disturbing anything the user set. A key already present is left alone —
# merge-policy.json gives `env` winner_on_conflict: user, and writing after
# the merge must honour the same rule.
kit_write_runtime_env() {
    local settings="${CLAUDE_HOME}/settings.json" computed
    computed="$(kit_compute_path)"
    log "Recording runtime environment in settings.json..."
    KIT_COMPUTED_PATH="${computed}" python3 - "${settings}" "${KIT_RUNTIME_ENV_KEYS_FILE}" <<'PY'
import json
import os
import sys

settings_path, keys_path = sys.argv[1], sys.argv[2]

# The values are computed here; the key NAMES come from the shared list, so
# diff-settings.py and uninstall.sh cannot fall out of step with this writer.
# CLAUDE_CODE_ENABLE_TODO_TOOLS turns on TaskCreate/TaskUpdate/TaskList/
# TaskGet, which rule 40's Pre-Dispatch Protocol is built on and which are
# opt-in on current model families.
values = {
    "PATH": os.environ["KIT_COMPUTED_PATH"],
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",
}

with open(keys_path, encoding="utf-8") as fh:
    keys = [ln.strip() for ln in fh
            if ln.strip() and not ln.lstrip().startswith("#")]

unknown = [k for k in keys if k not in values]
if unknown:
    sys.exit(f"  no value defined for runtime env key(s): {', '.join(unknown)}")

with open(settings_path, encoding="utf-8") as fh:
    data = json.load(fh)

env = data.setdefault("env", {})
# Only fill what the user has not set. Their values are theirs — including a
# deliberate opt-out, which is why this checks presence rather than truth.
added = [k for k in keys if k not in env]
for key in added:
    env[key] = values[key]

with open(settings_path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")

print("  " + (", ".join(added) + " set" if added
              else "already set by you; left alone"))
PY
}
