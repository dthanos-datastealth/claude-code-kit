#!/usr/bin/env python3
"""Break the kit on purpose, and check the tests notice.

A green suite says the code passes the tests. It does not say the tests would
fail if the code were wrong, and those are different claims. Twice in Iter-4 a
test was written specifically to cover a bug, reviewed, and could not fail for
that bug — one of them was the centrepiece of a BLOCKER fix.

Reverting a whole file does not find this. Reverting `scripts/_kit_env.sh`
wholesale breaks enough that something fails, so the file looks covered; the
same suite stays green when a single `:` moves from one side of a variable to
the other. So: change one thing, run the tests that claim to cover it, and
require them to fail.

Each mutant in scripts/mutants.json is a specific defect the kit has either
shipped before or would obviously regret. A mutant that SURVIVES is the
finding — it names a test that cannot fail.

Usage:
  mutate.py list                 # what is covered, and what each mutant breaks
  mutate.py run <id> [<id>...]   # run named mutants
  mutate.py run-all              # every mutant (CI form)

Exit 0 when every mutant run was killed, 1 when any survived.

Each run happens in a throwaway copy of the working tree, so the real
repository is never modified — including when a run is interrupted.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MUTANTS = Path(__file__).parent / "mutants.json"

# Copying the tree is the slow part, so skip what no test reads. tests/.tmp in
# particular holds isolated HOMEs from previous runs and can reach gigabytes.
IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", "*.pyc", ".tmp", ".pytest_cache",
)


def load_mutants() -> list[dict]:
    data = json.loads(MUTANTS.read_text())
    return data["mutants"]


def apply_mutant(tree: Path, mutant: dict) -> None:
    """Apply the mutation, or fail loudly if the anchor text is gone.

    A mutant whose `find` no longer matches is not a pass — it means the code
    moved and nobody updated the mutant, so it has been silently testing
    nothing. That is the same defect class this tool exists to catch, so it is
    an error rather than a skip.
    """
    target = tree / mutant["file"]
    text = target.read_text()
    find = mutant["find"]
    count = text.count(find)
    if count == 0:
        raise SystemExit(
            f"mutant {mutant['id']}: anchor text not found in {mutant['file']}.\n"
            f"  looked for: {find!r}\n"
            f"  The code moved and this mutant went stale — it has been "
            f"asserting nothing. Update scripts/mutants.json."
        )
    if count > 1:
        raise SystemExit(
            f"mutant {mutant['id']}: anchor text appears {count} times in "
            f"{mutant['file']}; it must be unique to mutate one thing.\n"
            f"  looked for: {find!r}"
        )
    target.write_text(text.replace(find, mutant["replace"]))


def run_mutant(mutant: dict, verbose: bool = False) -> bool:
    """Return True if the mutant was KILLED (i.e. the tests noticed)."""
    with tempfile.TemporaryDirectory(prefix="cck-mutate-") as tmp:
        tree = Path(tmp) / "repo"
        shutil.copytree(REPO, tree, ignore=IGNORE, symlinks=True)
        apply_mutant(tree, mutant)

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-x", *mutant["tests"]],
            cwd=tree, text=True, capture_output=True,
        )
        killed = proc.returncode != 0
        if verbose and not killed:
            print(proc.stdout[-3000:])
        return killed


def cmd_list() -> int:
    for m in load_mutants():
        print(f"{m['id']}")
        print(f"    file   {m['file']}")
        print(f"    tests  {' '.join(m['tests'])}")
        print(f"    breaks {m['breaks']}")
        if m.get("history"):
            print(f"    seen   {m['history']}")
        print()
    return 0


def cmd_run(ids: list[str] | None, verbose: bool) -> int:
    mutants = load_mutants()
    if ids:
        by_id = {m["id"]: m for m in mutants}
        unknown = [i for i in ids if i not in by_id]
        if unknown:
            raise SystemExit(f"unknown mutant(s): {', '.join(unknown)}")
        mutants = [by_id[i] for i in ids]

    survivors = []
    for m in mutants:
        killed = run_mutant(m, verbose=verbose)
        mark = "killed " if killed else "SURVIVED"
        print(f"  {mark}  {m['id']:38s} {' '.join(m['tests'])}")
        if not killed:
            survivors.append(m)

    print()
    print(f"{len(mutants) - len(survivors)}/{len(mutants)} killed")
    if survivors:
        print()
        print("SURVIVING MUTANTS — each names a test that cannot fail:")
        for m in survivors:
            print(f"\n  {m['id']}")
            print(f"    {m['breaks']}")
            print(f"    Tests that should have caught it: {' '.join(m['tests'])}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("ids", nargs="+")
    run.add_argument("-v", "--verbose", action="store_true",
                     help="print pytest output for surviving mutants")
    run_all = sub.add_parser("run-all")
    run_all.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "run":
        return cmd_run(args.ids, args.verbose)
    return cmd_run(None, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
