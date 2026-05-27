from tests.helpers import run_install


def test_memory_index_copied_to_user_memory_dir():
    r = run_install()
    # The kit copies MEMORY.md into ~/.claude/memory/MEMORY.md as a generic
    # global memory template. The project-specific encoded path is created
    # lazily by Claude Code itself on first use.
    dst = r.home / ".claude" / "memory" / "MEMORY.md"
    assert dst.exists(), "MEMORY.md should be installed at ~/.claude/memory/MEMORY.md"
    content = dst.read_text()
    assert "Memory Index" in content
    assert "Feedback" in content


def test_memory_index_not_overwritten_if_user_has_one():
    r = run_install()
    # Manually pre-create user MEMORY.md, then run install again
    user_mem = r.home / ".claude" / "memory" / "MEMORY.md"
    user_mem.write_text("# Custom user memory index\n")
    # Re-run install in the same HOME by invoking install.sh again
    import subprocess
    proc = subprocess.run(
        ["bash", str(__import__("pathlib").Path(__file__).resolve().parents[1] / "install.sh")],
        env={"HOME": str(r.home), "PATH": f"{r.fake_bin}:/usr/bin:/bin", "LANG": "C.UTF-8"},
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert user_mem.read_text() == "# Custom user memory index\n", \
        "existing user MEMORY.md must not be overwritten"
