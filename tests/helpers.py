"""Test helpers — run install.sh in an isolated HOME with a mocked `claude` CLI."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO / "install.sh"


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    home: Path
    fake_bin: Path
    claude_log: Path


def write_fake_claude(bin_dir: Path, log: Path) -> Path:
    """Write a fake `claude` CLI that logs all invocations to `log`."""
    fake = bin_dir / "claude"
    fake.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> "{log}"
        # Emulate `claude plugin list` returning empty initially
        if [ "$1" = "plugin" ] && [ "$2" = "list" ]; then
            echo "(no plugins installed)"
        fi
        exit 0
    """))
    fake.chmod(0o755)
    return fake


def run_install(
    *,
    preexisting_claude_md: str | None = None,
    preexisting_settings: str | None = None,
    extra_path_tools: list[str] | None = None,
    omit_claude_cli: bool = False,
) -> RunResult:
    """Invoke install.sh in an isolated HOME.

    Returns: RunResult with returncode, captured streams, paths, and the
    log of how the fake `claude` CLI was invoked.
    """
    tmp = REPO / "tests" / ".tmp"
    tmp.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="cck-", dir=tmp))
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

    env = {
        "HOME": str(home),
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "LANG": "C.UTF-8",
    }
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
