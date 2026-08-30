"""Shared helpers for app launchers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def reap_if_needed(proc: subprocess.Popen[bytes] | None) -> None:
    """Reap a Popen if it has already exited to avoid zombies."""
    if proc is None:
        return
    try:
        if proc.poll() is not None:
            proc.wait(timeout=0)
    except (OSError, subprocess.TimeoutExpired):
        pass


def normalize_title(title: str) -> str:
    """Normalize a window title for comparison (collapsed whitespace, lowercase)."""
    return re.sub(r"\s+", " ", title.strip().lower())


def read_cmdline(pid: int) -> list[str]:
    """Read /proc/<pid>/cmdline, returning argv as a list of strings."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return []
    return [p.decode(errors="surrogateescape") for p in raw.split(b"\0") if p]
