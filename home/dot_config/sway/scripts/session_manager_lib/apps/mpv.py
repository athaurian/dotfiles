"""mpv media player: state inspection and restore."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import APP_WAIT_TIMEOUT
from ..ipc import WindowEventWatcher
from ._common import read_cmdline, reap_if_needed


def get_mpv_info(pid: int) -> str:
    for arg in reversed(read_cmdline(pid)[1:]):
        if arg and not arg.startswith("-") and Path(arg).is_file():
            return arg
    return ""


def launch_mpv(node: dict, claimed_ids: set[int]) -> int | None:
    from .generic import wait_for_window_by_pid

    media_path = node.get("media_path", "")
    if not media_path or not Path(media_path).is_file():
        return None

    cmd = ["mpv", "--force-window", media_path]

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
                watcher, proc.pid, "mpv", timeout=APP_WAIT_TIMEOUT
            )
        finally:
            reap_if_needed(proc)

    if not win_id:
        return None
    claimed_ids.add(win_id)
    return win_id
