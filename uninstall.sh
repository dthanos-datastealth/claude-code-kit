#!/usr/bin/env bash
# claude-code-kit uninstaller — restores the latest backup of CLAUDE.md
# and settings.json. Idempotent: safe to run if no backups exist.
set -euo pipefail

CLAUDE_HOME="${HOME}/.claude"
BACKUP_ROOT="${CLAUDE_HOME}/backups"

log()  { printf '\033[1;34m[cck-uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[cck-uninstall]\033[0m %s\n' "$*" >&2; }

# Restoring is conditional on there being a backup; removing what the kit
# installed is not. An install onto a clean machine makes no backup at all, and
# an early exit here used to mean such a machine could never be uninstalled —
# the rules, docs and state files all stayed.
src=""
if [ -d "${BACKUP_ROOT}" ]; then
    # Most-recent backup directory (ISO timestamps sort lexicographically).
    # shellcheck disable=SC2012  # safe: names are ISO-8601 timestamps
    latest=$(ls -1 "${BACKUP_ROOT}" 2>/dev/null | sort | tail -n1)
    [ -n "${latest}" ] && src="${BACKUP_ROOT}/${latest}"
fi

if [ -n "${src}" ]; then
    log "Restoring from ${src}..."
else
    log "No backup to restore from; removing what the kit installed."
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in CLAUDE.md settings.json; do
    if [ -n "${src}" ] && [ -f "${src}/${f}" ]; then
        cp "${src}/${f}" "${CLAUDE_HOME}/${f}"
        log "  Restored ${f}"
    fi
done

# With no backup there is nothing to restore, and that is the common case: on
# a clean machine install.sh backs nothing up, because there was nothing there
# to back up. Leaving settings.json alone then means "leaving the kit
# completely" leaves 22 plugins, 6 marketplaces, effortLevel and the kit's env
# block behind for good. Subtract what the kit put there instead.
#
# Only entries whose value still matches what the kit ships are removed. A
# plugin the user has since flipped to false, or an effortLevel they changed,
# is a decision of theirs and stays.
if [ -z "${src}" ] && [ -f "${CLAUDE_HOME}/settings.json" ]; then
    if python3 - "${CLAUDE_HOME}/settings.json" "${REPO_DIR}/claude/settings.json" \
                 "${REPO_DIR}/scripts/kit-runtime-env-keys.txt" <<'PY'
import json
import pathlib
import sys

live_path, kit_path, keys_path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(live_path, encoding="utf-8") as fh:
    live = json.load(fh)
with open(kit_path, encoding="utf-8") as fh:
    kit = json.load(fh)

removed = []
for section in ("enabledPlugins", "extraKnownMarketplaces", "env"):
    live_section = live.get(section)
    if not isinstance(live_section, dict):
        continue
    for key, kit_value in (kit.get(section) or {}).items():
        if key in live_section and live_section[key] == kit_value:
            del live_section[key]
            removed.append(f"{section}.{key}")

# The runtime env keys are written by scripts/_kit_env.sh after the merge
# rather than shipped in the template, so the loop above never sees them.
# Read from the shared list so this cannot fall behind the writer.
runtime_keys = [
    ln.strip() for ln in pathlib.Path(keys_path).read_text().splitlines()
    if ln.strip() and not ln.lstrip().startswith("#")
] if pathlib.Path(keys_path).is_file() else []
for key in runtime_keys:
    if key in (live.get("env") or {}):
        del live["env"][key]
        removed.append(f"env.{key}")

if live.get("effortLevel") == kit.get("effortLevel"):
    del live["effortLevel"]
    removed.append("effortLevel")

# One cleanup pass, after every removal, rather than per-section inside the
# loop above.
for section in ("enabledPlugins", "extraKnownMarketplaces", "env"):
    if section in live and not live[section]:
        del live[section]

with open(live_path, "w", encoding="utf-8") as fh:
    json.dump(live, fh, indent=2)
    fh.write("\n")

print(f"  Removed {len(removed)} kit key(s) from settings.json" if removed
      else "  settings.json held no kit keys")
PY
    then :; else
        warn "  Could not clean settings.json; leaving it untouched"
    fi
fi

# Clean up kit state files (version marker, cache, conflicts) — these are
# kit-specific bookkeeping that must not survive an uninstall, otherwise a
# future fresh install would see stale markers and get confused.
for f in .kit-version .kit-version.history.jsonl; do
    if [ -f "${CLAUDE_HOME}/${f}" ]; then
        rm -f "${CLAUDE_HOME}/${f}"
        log "  Removed ${f}"
    fi
done
for d in .kit-cache .kit-conflicts; do
    if [ -d "${CLAUDE_HOME}/${d}" ]; then
        rm -rf "${CLAUDE_HOME:?}/${d}"
        log "  Removed ${d}/"
    fi
done

# The kit's rule files and reference docs are the kit's, so leaving the kit
# means removing them — otherwise every future session keeps loading kit rules
# from a kit that is no longer installed. 00-user-overrides.md is yours and
# stays, along with anything else you put in rules/.
if [ -d "${CLAUDE_HOME}/rules" ]; then
    removed=0
    for f in "${CLAUDE_HOME}/rules/"*-kit-*.md; do
        [ -e "${f}" ] || continue
        rm -f "${f}"
        removed=$((removed + 1))
    done
    if [ "${removed}" -gt 0 ]; then
        log "  Removed ${removed} kit rule file(s) from rules/"
    fi
    # Restore the user's own rule files from the backup, AFTER the deletion
    # above rather than before it. Restoring first would copy all six kit
    # files back only for the *-kit-*.md loop to delete them again on the
    # next line; only 00-user-overrides.md and the user's own files are
    # meant to survive, so copy only those.
    if [ -n "${src}" ] && [ -d "${src}/rules" ]; then
        restored=0
        for f in "${src}/rules/"*.md; do
            [ -e "${f}" ] || continue
            case "$(basename "${f}")" in
                *-kit-*.md) continue ;;
            esac
            cp "${f}" "${CLAUDE_HOME}/rules/"
            restored=$((restored + 1))
        done
        if [ "${restored}" -gt 0 ]; then
            log "  Restored ${restored} of your own rule file(s) from backup"
        fi
    fi
    # Only if nothing of yours is left in there.
    if rmdir "${CLAUDE_HOME}/rules" 2>/dev/null; then
        log "  Removed empty rules/"
    fi
fi

if [ -d "${CLAUDE_HOME}/docs" ]; then
    rm -rf "${CLAUDE_HOME:?}/docs"
    log "  Removed docs/"
fi

log "Done. Plugins remain installed; remove via 'claude plugin uninstall <name>' if desired."
