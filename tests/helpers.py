"""Test helpers — run install.sh in an isolated HOME with a mocked `claude` CLI."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO / "install.sh"

# Scratch space for isolated HOMEs, per pytest session rather than shared.
# A shared directory plus a session-end rmtree means two concurrent runs of this
# suite delete each other's working directories mid-test: the first to finish
# wipes the tree the second is still installing into, and the second reports
# several unrelated-looking failures. That happens for real whenever a review
# agent runs the suite while a developer does, in the same checkout.
TMP_ROOT = REPO / "tests" / ".tmp"
SESSION_TMP = TMP_ROOT / f"session-{os.getpid()}"


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    home: Path
    fake_bin: Path
    claude_log: Path


# The fake CLI reads its log path from the environment instead of having it
# baked in, so the script itself is identical for every run and can be written
# once per pytest process. That matters more than it looks: macOS charges
# roughly 180ms the first time a newly created executable is run, and nothing
# on re-exec, so writing a fresh one for each of the ~28 installs in this suite
# cost about five seconds. Each run symlinks to the shared copy, and symlinks
# do not pay the tax.
_FAKE_CLAUDE_BODY = """\
#!/usr/bin/env bash
echo "$@" >> "${CCK_FAKE_CLAUDE_LOG}"
# Emulate `claude plugin list` returning empty initially
if [ "$1" = "plugin" ] && [ "$2" = "list" ]; then
    echo "(no plugins installed)"
fi
exit 0
"""

_shared_fake_claude: Path | None = None


def _shared_claude() -> Path:
    """The one fake `claude` script this process execs, created on first use."""
    global _shared_fake_claude
    if _shared_fake_claude is None:
        SESSION_TMP.mkdir(parents=True, exist_ok=True)
        path = SESSION_TMP / "fake-claude.sh"
        path.write_text(_FAKE_CLAUDE_BODY)
        path.chmod(0o755)
        _shared_fake_claude = path
    return _shared_fake_claude


def write_fake_claude(bin_dir: Path, log: Path) -> Path:
    """Place a fake `claude` CLI in `bin_dir` that logs invocations to `log`.

    `log` is honoured through CCK_FAKE_CLAUDE_LOG, which run_install sets in the
    child environment; callers that exec the binary themselves must set it too.
    """
    fake = bin_dir / "claude"
    fake.symlink_to(_shared_claude())
    return fake


def run_install(
    *,
    preexisting_claude_md: str | None = None,
    preexisting_settings: str | None = None,
    extra_path_tools: list[str] | None = None,
    omit_claude_cli: bool = False,
    seed_claude_in: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> RunResult:
    """Invoke install.sh in an isolated HOME.

    `extra_path_tools` writes into fake_bin, which IS on PATH. To reproduce the
    real-world preflight failure — a prerequisite installed on disk but not on
    the PATH the installer inherits — use `seed_claude_in` instead: it plants an
    executable `claude` at $HOME/<that dir>, which is deliberately left off
    PATH. Pair it with `omit_claude_cli=True` so nothing satisfies `command -v`.

    `extra_env` merges into the child environment, for pointing the installer's
    search list at a controlled directory.

    Returns: RunResult with returncode, captured streams, paths, and the
    log of how the fake `claude` CLI was invoked.
    """
    SESSION_TMP.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="cck-", dir=SESSION_TMP))
    home = work / "home"
    home.mkdir()
    (home / ".claude").mkdir()

    if preexisting_claude_md is not None:
        (home / ".claude" / "CLAUDE.md").write_text(preexisting_claude_md)
    if preexisting_settings is not None:
        (home / ".claude" / "settings.json").write_text(preexisting_settings)

    fake_bin = work / "bin"
    fake_bin.mkdir()
    claude_log = work / "claude.log"
    claude_log.touch()
    if not omit_claude_cli:
        write_fake_claude(fake_bin, claude_log)

    # Always provide python3, git, gh, uv stubs that just succeed
    for tool in ["git", "gh", "uv", "python3"] + (extra_path_tools or []):
        # python3 must be REAL python so the merge step works; symlink it
        real = shutil.which(tool)
        if real:
            (fake_bin / tool).symlink_to(real)
        else:
            # Stub: always succeed
            stub = fake_bin / tool
            stub.write_text("#!/usr/bin/env bash\nexit 0\n")
            stub.chmod(0o755)

    if seed_claude_in is not None:
        seeded_dir = home / seed_claude_in
        seeded_dir.mkdir(parents=True, exist_ok=True)
        write_fake_claude(seeded_dir, claude_log)

    env = {
        "HOME": str(home),
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "CCK_FAKE_CLAUDE_LOG": str(claude_log),
    }
    env.update(extra_env or {})
    proc = subprocess.run(
        ["bash", str(INSTALL_SH)],
        env=env,
        text=True,
        capture_output=True,
    )
    return RunResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        home=home,
        fake_bin=fake_bin,
        claude_log=claude_log,
    )
