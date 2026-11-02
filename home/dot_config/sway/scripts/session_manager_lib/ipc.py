"""Sway/i3 IPC connections, window watchers, and tree helpers."""

from __future__ import annotations

import json
import logging
import os
import select
import socket
import stat
import struct
import subprocess
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any, Self

from .config import (
    IPC_REQUEST_TIMEOUT,
    IPC_SUBSCRIBE_TIMEOUT,
    WATCHER_JOIN_TIMEOUT,
    canonical_app_id,
    detect_backend,
)

log = logging.getLogger("session_manager")

# Sway and i3 use the same IPC wire format. Magic stays "i3-ipc".
MAGIC = b"i3-ipc"
HEADER = struct.Struct("=6sII")

MSG_RUN_COMMAND = 0
MSG_SUBSCRIBE = 2
MSG_GET_TREE = 4

EVENT_BIT = 1 << 31
EVENT_WINDOW = 3


class IpcError(OSError):
    """Error raised when the compositor's IPC socket cannot be reached or used.

    It is an ``OSError`` because every cause is an I/O failure on the
    socket: a missing socket file, a refused connection, a timeout, or a
    reply that cannot be parsed. Callers already guard IPC calls with
    ``except OSError`` to degrade gracefully, so the error has to be one.
    """


def _socket_from_binary(backend: str) -> str:
    """Ask i3 or Sway for its IPC socket path."""
    binary = "i3" if backend == "i3" else "sway"
    try:
        result = subprocess.run(
            [binary, "--get-socketpath"],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _socket_exists(path: str) -> bool:
    """Report whether a path is a socket file that still exists."""
    try:
        return stat.S_ISSOCK(os.stat(path).st_mode)
    except OSError:
        return False


def resolve_socket_path() -> str:
    """Find the live Sway/i3 IPC socket.

    SESSION_MANAGER_SOCK is an explicit override. Otherwise the backend's
    environment variable is preferred, then the other compositor's variable,
    then ``--get-socketpath`` from the matching binary. Candidates whose
    socket file no longer exists are skipped, so a value left over from a
    previous compositor run does not shadow the live socket.
    """
    explicit = os.environ.get("SESSION_MANAGER_SOCK", "").strip()
    if explicit:
        return explicit

    backend = detect_backend()
    primary, secondary = (
        ("I3SOCK", "SWAYSOCK") if backend == "i3" else ("SWAYSOCK", "I3SOCK")
    )
    candidates: list[str] = []
    for name in (primary, secondary):
        value = os.environ.get(name, "").strip()
        if value:
            candidates.append(value)

    for candidate in (backend, "i3" if backend == "sway" else "sway"):
        value = _socket_from_binary(candidate)
        if value:
            candidates.append(value)

    for path in candidates:
        if _socket_exists(path):
            return path
    if candidates:
        log.warning("no live compositor socket found, tried: %s", ", ".join(candidates))
    return ""


@dataclass(frozen=True)
class WindowEvent:
    """One compositor window event with its container and timestamp."""

    change: str
    container: dict[str, Any]
    timestamp: float


def _pid_for_x11_window(window_id: int) -> int:
    """Return the PID owning an X11 window id, or 0 when unknown.

    i3 container trees omit `pid`; Chromium, kitty, and GTK apps still set
    `_NET_WM_PID`, which xdotool and xprop can read.
    """
    if not window_id:
        return 0
    commands = (
        ["xdotool", "getwindowpid", str(window_id)],
        ["xprop", "-id", str(window_id), "_NET_WM_PID"],
    )
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode != 0:
            continue
        for token in result.stdout.replace("=", " ").split():
            if token.isdigit():
                return int(token)
    return 0


def node_pid(node: dict) -> int:
    """Return a PID for a container, filling i3's missing `pid` from X11."""
    pid = node.get("pid")
    if isinstance(pid, int) and pid > 0:
        return pid
    window_id = node.get("window")
    if isinstance(window_id, int):
        return _pid_for_x11_window(window_id)
    return 0


class IpcConnection:
    """One Sway/i3 IPC socket for request/reply. Subscriptions need a
    dedicated instance.
    """

    def __init__(
        self,
        sock_path: str | None = None,
        request_timeout: float | None = IPC_REQUEST_TIMEOUT,
    ) -> None:
        self.sock_path = sock_path or resolve_socket_path()
        if not self.sock_path:
            raise IpcError(
                "no window manager IPC socket found "
                "(set SWAYSOCK, I3SOCK, or SESSION_MANAGER_SOCK)"
            )
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self.request_timeout = request_timeout

    # -- lifecycle -----------------------------------------------------

    def connect(self) -> IpcConnection:
        """Connect to the IPC socket and return this connection."""
        self.close()
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(self.sock_path)
        except OSError as exc:
            s.close()
            raise IpcError(f"cannot connect to {self.sock_path}: {exc}") from exc
        self._sock = s
        return self

    def close(self) -> None:
        """Close the socket and drop the connection."""
        s = self._sock
        self._sock = None
        if s is None:
            return
        try:
            s.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            s.close()
        except OSError:
            pass

    def __enter__(self) -> Self:
        if self._sock is None:
            self.connect()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- wire ----------------------------------------------------------

    def _send(self, msg_type: int, payload: str | bytes = b"") -> None:
        """Send one framed IPC message."""
        if self._sock is None:
            raise IpcError("socket not connected")
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        self._sock.sendall(HEADER.pack(MAGIC, len(body), msg_type) + body)

    def _read_exact(self, n: int, deadline: float | None) -> bytes:
        """Read exactly n bytes, honouring an optional deadline."""
        s = self._sock
        if s is None:
            raise IpcError("socket not connected")

        chunks: list[bytes] = []
        remaining = n

        while remaining:
            if deadline is not None:
                wait = deadline - time.monotonic()
                if wait <= 0:
                    raise TimeoutError("IPC read timeout")
                try:
                    readable, _, _ = select.select([s], [], [], wait)
                except OSError as exc:
                    raise IpcError("socket closed during select") from exc
                if not readable:
                    if chunks:
                        # Part of a message was read, so the stream is out
                        # of step and cannot be reused.
                        raise IpcError("IPC read timed out mid-message")
                    raise TimeoutError("IPC read timeout")

            try:
                chunk = s.recv(remaining)
            except OSError as exc:
                raise IpcError("socket closed during recv") from exc

            if not chunk:
                raise IpcError("socket closed by Sway")

            chunks.append(chunk)
            remaining -= len(chunk)

        return b"".join(chunks)

    def _recv(self, timeout: float | None = None) -> tuple[int, Any]:
        """Read one IPC message and return its type and decoded payload."""
        deadline = None if timeout is None else time.monotonic() + timeout
        magic, length, msg_type = HEADER.unpack(self._read_exact(HEADER.size, deadline))
        if magic != MAGIC:
            raise IpcError(f"bad IPC magic: {magic!r}")
        body = self._read_exact(length, deadline) if length else b""
        return msg_type, (json.loads(body.decode("utf-8")) if body else None)

    # -- requests ------------------------------------------------------

    def command(self, cmd: str, *, timeout: float | None = None) -> list[dict]:
        """Run a compositor command. Return per-command results without
        raising on failure.
        """
        with self._lock:
            try:
                self._send(MSG_RUN_COMMAND, cmd)
                msg_type, payload = self._recv(
                    self.request_timeout if timeout is None else timeout
                )
            except (TimeoutError, IpcError, OSError):
                # The reply may be half-read, so the stream is no longer
                # usable. Drop it and let the next call reconnect.
                self.close()
                raise
        if msg_type != MSG_RUN_COMMAND:
            raise IpcError(f"expected RUN_COMMAND reply, got {msg_type}")
        return payload if isinstance(payload, list) else []

    def command_checked(self, cmd: str, *, timeout: float | None = None) -> list[dict]:
        """Run a command and raise when the compositor reports failure."""
        result = self.command(cmd, timeout=timeout)
        bad = [r for r in result if not r.get("success", False)]
        if bad:
            raise IpcError(f"command failed: {cmd!r} -> {bad}")
        return result

    def get_tree(self, *, timeout: float | None = None) -> dict[str, Any]:
        """Return the current compositor tree."""
        with self._lock:
            try:
                self._send(MSG_GET_TREE)
                msg_type, payload = self._recv(
                    self.request_timeout if timeout is None else timeout
                )
            except (TimeoutError, IpcError, OSError):
                self.close()
                raise
        if msg_type != MSG_GET_TREE:
            raise IpcError(f"expected GET_TREE reply, got {msg_type}")
        if not isinstance(payload, dict):
            raise IpcError(f"GET_TREE returned {type(payload).__name__}")
        return payload


class WindowEventWatcher:
    """Window event stream on a dedicated IPC connection."""

    def __init__(self, sock_path: str | None = None) -> None:
        self._conn = IpcConnection(sock_path).connect()
        try:
            with self._conn._lock:
                self._conn._send(MSG_SUBSCRIBE, json.dumps(["window"]))
                msg_type, reply = self._conn._recv(timeout=IPC_SUBSCRIBE_TIMEOUT)
        except Exception:
            self._conn.close()
            raise
        if msg_type != MSG_SUBSCRIBE:
            self._conn.close()
            raise IpcError(f"expected SUBSCRIBE reply, got {msg_type}")
        ok = reply.get("success") if isinstance(reply, dict) else False
        if not ok:
            self._conn.close()
            raise IpcError(f"SUBSCRIBE rejected: {reply!r}")

        self._queue: Queue[WindowEvent] = Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        """Read window events until the watcher is closed."""
        while not self._stop.is_set():
            try:
                msg_type, payload = self._conn._recv(timeout=0.25)
            except TimeoutError:
                continue
            except (IpcError, OSError) as exc:
                if not self._stop.is_set():
                    log.warning("window event stream terminated: %s", exc)
                return

            if not (msg_type & EVENT_BIT):
                continue
            if (msg_type & ~EVENT_BIT) != EVENT_WINDOW:
                continue
            if not isinstance(payload, dict):
                continue

            container = payload.get("container")
            self._queue.put(
                WindowEvent(
                    change=payload.get("change", ""),
                    container=container if isinstance(container, dict) else {},
                    timestamp=time.monotonic(),
                )
            )

    def get(self, timeout: float) -> WindowEvent | None:
        """Wait for the next window event, or return None on timeout."""
        try:
            return self._queue.get(timeout=max(0.0, timeout))
        except Empty:
            return None

    def close(self) -> None:
        """Stop the reader thread and close the connection."""
        self._stop.set()
        self._conn.close()
        if self._thread.is_alive():
            self._thread.join(timeout=WATCHER_JOIN_TIMEOUT)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


# Shared connection + convenience wrappers

_shared: IpcConnection | None = None
_shared_lock = threading.Lock()


def connection() -> IpcConnection:
    """Return the lazily created process-wide command/query connection."""
    global _shared
    with _shared_lock:
        if _shared is None or _shared._sock is None:
            # A closed connection means the previous one was dropped after
            # a failure, so a fresh socket is needed.
            if _shared is not None:
                _shared.close()
            _shared = IpcConnection().connect()
        return _shared


def close_connection() -> None:
    """Close and forget the process-wide connection."""
    global _shared
    with _shared_lock:
        if _shared is not None:
            _shared.close()
            _shared = None


def run_command(cmd: str) -> list[dict]:
    """Run a compositor command without raising on failure."""
    return connection().command(cmd)


def run_command_logged(cmd: str) -> bool:
    """Run a compositor command and warn on failure.

    Return True when all subcommands succeed.
    """
    result = run_command(cmd)
    bad = [r for r in result if not r.get("success", False)]
    if bad:
        log.warning("window manager command failed: %s -> %s", cmd, bad)
        return False
    return True


def get_tree() -> dict[str, Any]:
    """Return the current compositor tree."""
    return connection().get_tree()


# Tree helpers


def walk_tree(node: dict) -> Iterator[dict]:
    """Yield every node in a tree, depth-first."""
    yield node
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        yield from walk_tree(child)


def node_class(node: dict) -> str:
    """Return the X11 WM_CLASS name."""
    props = node.get("window_properties") or {}
    return props.get("class") or node.get("class") or ""


def node_instance(node: dict) -> str:
    """Return the X11 WM_CLASS instance, which i3 uses for drop terminals."""
    props = node.get("window_properties") or {}
    return props.get("instance") or node.get("instance") or ""


def node_app_id(node: dict) -> str:
    """Return a canonical app identity for a Wayland or X11 window.

    Sway exposes ``app_id`` for native Wayland clients and ``WM_CLASS`` for
    XWayland clients. i3 only has ``WM_CLASS``. Both are normalized to the
    lower-case identifiers stored in session files.
    """
    raw = node.get("app_id") or node_class(node) or node_instance(node) or ""
    return canonical_app_id(raw)


def matches_app(node: dict, app_id: str, class_name: str) -> bool:
    """Report whether a live container matches a saved app identity."""
    requested = canonical_app_id(app_id)
    live = node_app_id(node)

    if requested:
        # A native Wayland app_id is authoritative: do not claim an
        # unrelated window just because its X11 class matches. On i3 the
        # canonical WM_CLASS already lives in `live`.
        return live == requested

    return bool(
        class_name
        and canonical_app_id(node_class(node)) == canonical_app_id(class_name)
    )


def is_window_node(node: dict) -> bool:
    """Report whether a node represents a window."""
    if node.get("type") not in ("con", "floating_con"):
        return False
    if node.get("id") is None:
        return False
    return bool(
        node.get("app_id")
        or node.get("pid")
        or node.get("window")
        or node.get("window_properties")
    )


def matching_window_ids_in_tree(
    tree: dict[str, Any], app_id: str, class_name: str
) -> list[int]:
    """Return the window ids in a tree that match an app identity."""
    return [
        n["id"]
        for n in walk_tree(tree)
        if n.get("type") in ("con", "floating_con")
        and matches_app(n, app_id, class_name)
        and n.get("id") is not None
    ]


def matching_window_ids(app_id: str, class_name: str) -> list[int]:
    """Return the ids of live windows that match an app identity."""
    return matching_window_ids_in_tree(get_tree(), app_id, class_name)
