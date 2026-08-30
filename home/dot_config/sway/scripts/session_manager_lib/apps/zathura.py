"""Zathura document viewer: state inspection and restore."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from ..config import (
    APP_WAIT_TIMEOUT,
    ZATHURA_DBUS_TIMEOUT,
    ZATHURA_GOTO_PAGE_DEADLINE,
)
from ..ipc import WindowEventWatcher
from ._common import read_cmdline, reap_if_needed


def get_zathura_info(pid: int) -> tuple[str, int]:
    bus_name = f"org.pwmt.zathura.PID-{pid}"
    doc_path, page_num = "", 0
    try:
        r = subprocess.run(
            [
                "busctl",
                "--user",
                "get-property",
                bus_name,
                "/org/pwmt/zathura",
                "org.pwmt.zathura",
                "filename",
            ],
            capture_output=True,
            text=True,
            timeout=ZATHURA_DBUS_TIMEOUT,
            check=False,
        )
        if r.returncode == 0 and '"' in r.stdout:
            doc_path = r.stdout.split('"')[1]
    except (subprocess.SubprocessError, OSError, ValueError):
        pass

    if doc_path:
        try:
            r = subprocess.run(
                [
                    "busctl",
                    "--user",
                    "get-property",
                    bus_name,
                    "/org/pwmt/zathura",
                    "org.pwmt.zathura",
                    "pagenumber",
                ],
                capture_output=True,
                text=True,
                timeout=ZATHURA_DBUS_TIMEOUT,
                check=False,
            )
            if r.returncode == 0:
                page_num = int(r.stdout.split()[-1])
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
        return doc_path, page_num

    for arg in read_cmdline(pid)[1:]:
        if arg and not arg.startswith("-") and Path(arg).is_file():
            return arg, 0
    return "", 0


def launch_zathura(node: dict, claimed_ids: set[int]) -> int | None:
    from .generic import wait_for_window_by_pid

    doc_path = node.get("document_path", "")
    page_num = node.get("page_number", 0)

    cmd: list[str] = ["zathura"]
    if doc_path and Path(doc_path).is_file():
        cmd.append(doc_path)

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
                watcher, proc.pid, "org.pwmt.zathura", timeout=APP_WAIT_TIMEOUT
            )
        finally:
            reap_if_needed(proc)

    if not win_id:
        return None
    claimed_ids.add(win_id)

    if page_num and doc_path:
        # D-Bus name is only registered after the document loads. Poll the
        # bus instead of sleeping blindly.
        bus_name = f"org.pwmt.zathura.PID-{proc.pid}"
        deadline = time.monotonic() + ZATHURA_GOTO_PAGE_DEADLINE
        while time.monotonic() < deadline:
            r = subprocess.run(
                [
                    "busctl",
                    "--user",
                    "call",
                    bus_name,
                    "/org/pwmt/zathura",
                    "org.pwmt.zathura",
                    "GotoPage",
                    "u",
                    str(page_num),
                ],
                capture_output=True,
                timeout=ZATHURA_DBUS_TIMEOUT,
                check=False,
            )
            if r.returncode == 0:
                break
            time.sleep(0.1)

    return win_id
