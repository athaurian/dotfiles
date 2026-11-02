"""Compositor environment repair for restored apps.

A restore can be triggered from a login script, a systemd unit, or a cron
job whose environment lacks the compositor's display variables. The apps
launched during the restore then fail to connect to X11 or Wayland and never
appear. This module copies the missing variables from the running compositor
into the current process environment.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .config import detect_backend
from .ipc import resolve_socket_path

log = logging.getLogger("session_manager")

# Root of the proc filesystem. Tests point this at a fake tree.
PROC_ROOT = Path("/proc")


def _read_environ(pid: int) -> dict[str, str]:
    """Return a process's environment variables."""
    try:
        raw = (PROC_ROOT / str(pid) / "environ").read_bytes()
    except OSError:
        return {}
    env: dict[str, str] = {}
    for item in raw.split(b"\0"):
        key, sep, value = item.partition(b"=")
        if not sep:
            continue
        env[key.decode(errors="replace")] = value.decode(errors="replace")
    return env


def _find_pids(name: str) -> list[int]:
    """Return the PIDs of the running processes named `name`."""
    pids: list[int] = []
    try:
        entries = os.listdir(PROC_ROOT)
    except OSError:
        return pids
    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            comm = (PROC_ROOT / entry / "comm").read_text().strip()
        except OSError:
            continue
        if comm == name:
            pids.append(int(entry))
    return pids


def _socket_inodes(pid: int) -> set[str]:
    """Return the socket inodes the process has open."""
    fd_dir = PROC_ROOT / str(pid) / "fd"
    inodes: set[str] = set()
    try:
        entries = os.listdir(fd_dir)
    except OSError:
        return inodes
    for entry in entries:
        try:
            target = os.readlink(fd_dir / entry)
        except OSError:
            continue
        if target.startswith("socket:[") and target.endswith("]"):
            inodes.add(target[8:-1])
    return inodes


def _socket_paths(pid: int) -> list[str]:
    """Return the Unix socket paths the process has open."""
    inodes = _socket_inodes(pid)
    if not inodes:
        return []
    try:
        raw = (PROC_ROOT / "net" / "unix").read_text(errors="replace")
    except OSError:
        return []
    paths = []
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[6] in inodes:
            paths.append(fields[7])
    return paths


def _compositor_pid(backend: str) -> int:
    """Return the compositor process that owns the session's IPC socket."""
    name = "i3" if backend == "i3" else "sway"
    pids = _find_pids(name)
    if not pids:
        return 0
    if len(pids) == 1:
        return pids[0]
    socket_path = resolve_socket_path()
    if socket_path:
        for pid in pids:
            if socket_path in _socket_paths(pid):
                return pid
    return pids[0]


def _ipc_socket_path(sockets: list[str], marker: str) -> str:
    """Return the compositor's IPC socket path from its open sockets."""
    for path in sockets:
        if marker in os.path.basename(path):
            return path
    return ""


def _fill_in(env: dict[str, str], key: str, value: str | None) -> None:
    """Fill in a variable the caller does not have.

    An existing value is kept, but a value that disagrees with the
    compositor's is reported, because the restored apps would then talk to
    the wrong display server.
    """
    if not value:
        return
    current = env.get(key)
    if current:
        if current != value:
            log.warning("%s is %s but the compositor uses %s", key, current, value)
        return
    env[key] = value


def compositor_env() -> dict[str, str]:
    """Return the environment that restored apps should run with.

    The caller's environment is the base. Only the variables the compositor's
    clients need are filled in, and only when they are missing, so a caller
    that already knows the right display keeps it.
    """
    env = dict(os.environ)
    backend = detect_backend()
    pid = _compositor_pid(backend)
    if not pid:
        return env

    compositor = _read_environ(pid)
    sockets = _socket_paths(pid)

    if backend == "i3":
        # i3 is an X11 client, so its own environment names the display.
        _fill_in(env, "DISPLAY", compositor.get("DISPLAY"))
        _fill_in(env, "XAUTHORITY", compositor.get("XAUTHORITY"))
        _fill_in(env, "I3SOCK", _ipc_socket_path(sockets, "ipc-socket"))
        return env

    # Sway does not export WAYLAND_DISPLAY to itself, so it comes from the
    # Wayland socket the compositor has open.
    if not env.get("WAYLAND_DISPLAY"):
        for path in sockets:
            name = os.path.basename(path)
            if name.startswith("wayland-"):
                env["WAYLAND_DISPLAY"] = name
                runtime_dir = os.path.dirname(path)
                if runtime_dir:
                    env.setdefault("XDG_RUNTIME_DIR", runtime_dir)
                break
    elif not env.get("XDG_RUNTIME_DIR"):
        fallback_dir = compositor.get("XDG_RUNTIME_DIR")
        if fallback_dir:
            env["XDG_RUNTIME_DIR"] = fallback_dir
    _fill_in(env, "XAUTHORITY", compositor.get("XAUTHORITY"))
    _fill_in(env, "SWAYSOCK", _ipc_socket_path(sockets, "sway-ipc"))
    return env


def apply_compositor_env() -> bool:
    """Add the compositor's display variables to this process's environment.

    Every app the restore launches inherits os.environ, so filling the gaps
    once here covers all of them. Return True when something was added.
    """
    changed = False
    for key, value in compositor_env().items():
        if value and not os.environ.get(key):
            os.environ[key] = value
            changed = True
    return changed
