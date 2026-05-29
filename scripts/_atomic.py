"""Atomic write helpers shared by scripts/intelligent-*-merge.py.

Eliminates the previously-duplicated tmpfile+os.replace pattern in
intelligent-settings-merge.py (JSON) and intelligent-claude-md-merge.py
(text). Both files now import from here.
"""
from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _atomic_write(path: Path, body: str, prefix: str, suffix: str) -> None:
    """Write `body` to `path` atomically. tmpfile + os.replace pattern."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=prefix, suffix=suffix)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def atomic_write_text(path: Path, text: str) -> None:
    """Atomically write `text` to `path`."""
    _atomic_write(path, text, prefix=".cck-", suffix=".tmp")


def atomic_write_json(path: Path, data: Any) -> None:
    """Atomically write `data` as pretty-printed JSON to `path`.
    Trailing newline added (matches kit's JSON-on-disk convention)."""
    body = json.dumps(data, indent=2, sort_keys=False) + "\n"
    _atomic_write(path, body, prefix=".cck-", suffix=".json")
