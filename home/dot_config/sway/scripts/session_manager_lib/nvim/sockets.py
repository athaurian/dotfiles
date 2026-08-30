"""Neovim runtime socket discovery and PID extraction."""

from __future__ import annotations

import os
from pathlib import Path


def sock_pid(socket: Path) -> int | None:
    """Extract PID from nvim.<PID>.0 socket filename."""
    parts = socket.name.split(".")
    try:
        return int(parts[1])
    except (IndexError, ValueError):
        return None


def runtime_dir() -> Path:
    return Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))


def nvim_socket_path(pid: int) -> Path:
    return runtime_dir() / f"nvim.{pid}.0"


def runtime_nvim_sockets() -> list[Path]:
    runtime = runtime_dir()
    result = []
    try:
        for entry in runtime.iterdir():
            if entry.name.startswith("nvim.") and entry.is_socket():
                result.append(entry)
    except OSError:
        pass
    return sorted(result)
