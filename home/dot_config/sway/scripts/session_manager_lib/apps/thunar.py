"""Thunar file manager: state inspection and restore."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import APP_WAIT_TIMEOUT
from ..ipc import WindowEventWatcher
from ._common import read_cmdline, reap_if_needed


def get_thunar_info(pid: int) -> str:
    for arg in reversed(read_cmdline(pid)[1:]):
        if arg and not arg.startswith("-") and Path(arg).is_dir():
            return arg
    # Fallback to cmdline folder or window title parsing not needed
    # Try to infer from /proc cwd if no arg
    try:
        cwd = Path(f"/proc/{pid}/cwd").readlink()
        if cwd.is_dir():
            return str(cwd)
    except OSError:
        pass
    return ""


def launch_thunar(node: dict, claimed_ids: set[int]) -> int | None:
    from .generic import wait_for_window_by_pid

    folder = node.get("folder_path", "")
    # Validate folder exists, else fallback to home
    if not folder or not Path(folder).is_dir():
        folder = str(Path.home())

    cmd = ["thunar", folder]

    proc = None
    with WindowEventWatcher() as watcher:
        proc = subprocess.Popen(
            cmd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            win_id = wait_for_window_by_pid(
                watcher, proc.pid, "thunar", timeout=APP_WAIT_TIMEOUT
            )
        finally:
            reap_if_needed(proc)

    if not win_id:
        return None
    claimed_ids.add(win_id)
    return win_id
