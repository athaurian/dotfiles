"""Foot terminal: nvim session argument building, launch logic."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

from ..config import FOOT_WAIT_TIMEOUT
from ..ipc import WindowEventWatcher
from ._common import reap_if_needed

log = logging.getLogger("session_manager")


def _zellij_args(node: dict) -> list[str] | None:
    sess = node.get("zellij_session")
    if sess and isinstance(sess, str):
        # Saved as "zellij" for bare zellij without named session
        if sess == "zellij":
            return ["zellij"]
        return ["zellij", "attach", "-c", sess]
    return None


def build_foot_nvim_args(node: dict) -> list[str]:
    # Zellij takes precedence over nvim
    z_args = _zellij_args(node)
    if z_args is not None:
        return z_args

    was_ssh = node.get("was_ssh")
    if was_ssh and isinstance(was_ssh, str):
        # Leave a clue for the user to reconnect, don't auto-run ssh (needs password)
        safe = shlex.quote(was_ssh)
        return ["bash", "-ic", f"echo 'was: {safe} — press Up to reconnect'; exec bash"]

    nvim_type = node.get("nvim_type", "none")
    snapshot_path_str = node.get("nvim_snapshot", "")
    snacks_sidecar_str = node.get("nvim_snacks_sidecar", "")
    session_path_str = node.get("session_file", "")

    if (
        nvim_type == "session"
        and snapshot_path_str
        and Path(snapshot_path_str).is_file()
    ):
        safe_snapshot = shlex.quote(snapshot_path_str)
        lua_parts = [
            (
                "local f=os.getenv('NVIM_RESTORE_FILE'); "
                "if f then vim.cmd('source ' .. vim.fn.fnameescape(f)) end"
            ),
        ]
        snacks_sidecar = Path(snacks_sidecar_str) if snacks_sidecar_str else None
        if snacks_sidecar and snacks_sidecar.exists():
            try:
                content = snacks_sidecar.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                if content == "1":
                    lua_parts.append(
                        "vim.defer_fn(function() "
                        "pcall(require, 'snacks') "
                        "pcall(Snacks.explorer) "
                        "end, 300)"
                    )
            except OSError:
                pass
        full_lua = "; ".join(lua_parts)
        shell_cmd = (
            f"NVIM_RESTORE_SESSION=1 "
            f"NVIM_RESTORE_FILE={safe_snapshot} "
            f"nvim -c {shlex.quote('lua ' + full_lua)}; exec bash"
        )
        return ["bash", "-ic", shell_cmd]

    if nvim_type == "dashboard":
        return ["nvim", "bash"]

    if (
        nvim_type in ("unknown", "session")
        and session_path_str
        and Path(session_path_str).is_file()
    ):
        safe_session = shlex.quote(session_path_str)
        log.info("Restoring foot nvim from legacy session file: %s", session_path_str)
        lua_cmd = (
            "local f=os.getenv('NVIM_RESTORE_FILE'); "
            "if f then vim.cmd('source ' .. vim.fn.fnameescape(f)) end"
        )
        shell_cmd = (
            f"NVIM_RESTORE_SESSION=1 NVIM_RESTORE_FILE={safe_session} "
            f"nvim -c {shlex.quote('lua ' + lua_cmd)}; exec bash"
        )
        return ["bash", "-ic", shell_cmd]

    return ["bash"]


def launch_foot(
    node: dict, claimed_ids: set[int], *, app_id: str = "foot"
) -> int | None:
    from .generic import wait_for_window_by_pid

    cwd = node.get("cwd", str(Path.home()))
    title = node.get("name", "foot")

    if app_id == "foot_drop":
        cmd: list[str] = ["foot", "--app-id=foot_drop", "--working-directory", cwd]
    else:
        if not title or title == "foot":
            user = os.getenv("USER", "user")
            host = os.uname().nodename.split(".")[0]
            home = str(Path.home())
            short_cwd = (
                "~"
                if cwd == home
                else (f"~{cwd[len(home) :]}" if cwd.startswith(home + "/") else cwd)
            )
            title = f"{user}@{host}:{short_cwd}"
        cmd = ["foot", "--working-directory", cwd, "--title", title]

    cmd += build_foot_nvim_args(node)

    proc = None
    with WindowEventWatcher() as watcher:
        proc = subprocess.Popen(cmd, start_new_session=True)
        try:
            win_id = wait_for_window_by_pid(
                watcher, proc.pid, app_id, timeout=FOOT_WAIT_TIMEOUT
            )
        finally:
            reap_if_needed(proc)

    if win_id:
        claimed_ids.add(win_id)
        return win_id
    return None


def launch_foot_drop(node: dict, claimed_ids: set[int]) -> int | None:
    return launch_foot(node, claimed_ids, app_id="foot_drop")
