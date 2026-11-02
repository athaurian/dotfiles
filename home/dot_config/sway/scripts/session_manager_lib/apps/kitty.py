"""Kitty terminal launch and nvim session arguments."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

from ..config import (
    DROP_TERMINAL_INSTANCE,
    DROP_TERMINAL_TITLE,
    TERMINAL_WAIT_TIMEOUT,
)
from ..ipc import WindowEventWatcher
from ._common import reap_if_needed

log = logging.getLogger("session_manager")


def _zellij_args(node: dict) -> list[str] | None:
    """Return the zellij launch arguments for a saved node, if any."""
    sess = node.get("zellij_session")
    if sess and isinstance(sess, str):
        # Saved as "zellij" for bare zellij without named session
        if sess == "zellij":
            return ["zellij"]
        return ["zellij", "attach", "-c", sess]
    return None


def build_kitty_nvim_args(node: dict) -> list[str]:
    """Build the shell command that restores a terminal's programs."""
    # Zellij takes precedence over nvim
    z_args = _zellij_args(node)
    if z_args is not None:
        return z_args

    was_ssh = node.get("was_ssh")
    if was_ssh and isinstance(was_ssh, str):
        # Do not auto-run ssh, because it needs a password. Leave a reconnect
        # hint for the user instead.
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
        return ["nvim"]

    if (
        nvim_type in ("unknown", "session")
        and session_path_str
        and Path(session_path_str).is_file()
    ):
        safe_session = shlex.quote(session_path_str)
        log.info("Restoring kitty nvim from legacy session file: %s", session_path_str)
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


def build_kitty_command(node: dict, *, drop: bool = False) -> list[str]:
    """Build the kitty launch command for a saved node."""
    cwd = node.get("cwd", str(Path.home()))
    if drop:
        # `--name` sets the X11 WM_CLASS instance (the class stays "kitty"),
        # which is what the window manager's `for_window` rule matches on.
        # Without it the rule never fires, so the dropdown would not pick up
        # its floating size, mark, and scratchpad placement until the next
        # toggle. `--title` keeps the window name stable across saves.
        return [
            "kitty",
            f"--name={DROP_TERMINAL_INSTANCE}",
            f"--title={DROP_TERMINAL_TITLE}",
            "--directory",
            cwd,
        ] + build_kitty_nvim_args(node)

    title = node.get("name", "kitty")
    if not title or title == "kitty":
        user = os.getenv("USER", "user")
        host = os.uname().nodename.split(".")[0]
        home = str(Path.home())
        short_cwd = (
            "~"
            if cwd == home
            else (f"~{cwd[len(home) :]}" if cwd.startswith(home + "/") else cwd)
        )
        title = f"{user}@{host}:{short_cwd}"
    return ["kitty", "--directory", cwd, "--title", title] + build_kitty_nvim_args(node)


def launch_kitty(
    node: dict, claimed_ids: set[int], *, drop: bool = False
) -> int | None:
    """Launch a kitty terminal and return its window id."""
    from .generic import wait_for_window_by_pid

    cmd = build_kitty_command(node, drop=drop)

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
                watcher, proc.pid, "kitty", timeout=TERMINAL_WAIT_TIMEOUT
            )
        finally:
            reap_if_needed(proc)

    if win_id:
        claimed_ids.add(win_id)
        return win_id
    return None


def launch_kitty_drop(node: dict, claimed_ids: set[int]) -> int | None:
    """Launch the dropdown terminal and return its window id."""
    return launch_kitty(node, claimed_ids, drop=True)
