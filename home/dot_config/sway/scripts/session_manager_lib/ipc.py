"""Sway IPC: connections, window watchers, and tree helpers."""

from __future__ import annotations

import json
import logging
import os
import select
import socket
import struct
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
)

log = logging.getLogger("session_manager")

# Sway uses the i3 IPC wire format. Magic stays "i3-ipc" for compatibility.
MAGIC = b"i3-ipc"
HEADER = struct.Struct("=6sII")

MSG_RUN_COMMAND = 0
MSG_SUBSCRIBE = 2
MSG_GET_TREE = 4

EVENT_BIT = 1 << 31
EVENT_WINDOW = 3


class IpcError(RuntimeError):
    pass


@dataclass(frozen=True)
class WindowEvent:
    change: str
    container: dict[str, Any]
    timestamp: float


class IpcConnection:
    """One Sway IPC socket for request/reply. Use a dedicated instance for subscriptions."""

    def __init__(
        self,
        sock_path: str | None = None,
        request_timeout: float | None = IPC_REQUEST_TIMEOUT,
    ) -> None:
        self.sock_path = sock_path or os.environ.get("SWAYSOCK", "")
        if not self.sock_path:
            raise IpcError("SWAYSOCK is not set")
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()
        self.request_timeout = request_timeout

    # -- lifecycle -----------------------------------------------------

    def connect(self) -> IpcConnection:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self.sock_path)
        self._sock = s
        return self

    def close(self) -> None:
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
        if self._sock is None:
            raise IpcError("socket not connected")
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        self._sock.sendall(HEADER.pack(MAGIC, len(body), msg_type) + body)

    def _read_exact(self, n: int, deadline: float | None) -> bytes:
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
        deadline = None if timeout is None else time.monotonic() + timeout
        magic, length, msg_type = HEADER.unpack(self._read_exact(HEADER.size, deadline))
        if magic != MAGIC:
            raise IpcError(f"bad IPC magic: {magic!r}")
        body = self._read_exact(length, deadline) if length else b""
        return msg_type, (json.loads(body.decode("utf-8")) if body else None)

    # -- requests ------------------------------------------------------

    def command(self, cmd: str, *, timeout: float | None = None) -> list[dict]:
        """Run a Sway command. Returns per-command results; never raises on Sway failure."""
        with self._lock:
            self._send(MSG_RUN_COMMAND, cmd)
            msg_type, payload = self._recv(
                self.request_timeout if timeout is None else timeout
            )
        if msg_type != MSG_RUN_COMMAND:
            raise IpcError(f"expected RUN_COMMAND reply, got {msg_type}")
        return payload if isinstance(payload, list) else []

    def command_checked(self, cmd: str, *, timeout: float | None = None) -> list[dict]:
        """Run a command and raise if Sway reported failure."""
        result = self.command(cmd, timeout=timeout)
        bad = [r for r in result if not r.get("success", False)]
        if bad:
            raise IpcError(f"command failed: {cmd!r} -> {bad}")
        return result

    def get_tree(self, *, timeout: float | None = None) -> dict[str, Any]:
        with self._lock:
            self._send(MSG_GET_TREE)
            msg_type, payload = self._recv(
                self.request_timeout if timeout is None else timeout
            )
        if msg_type != MSG_GET_TREE:
            raise IpcError(f"expected GET_TREE reply, got {msg_type}")
        if not isinstance(payload, dict):
            raise IpcError(f"GET_TREE returned {type(payload).__name__}")
        return payload


class WindowEventWatcher:
    """Window event stream on a dedicated IPC connection."""

    def __init__(self, sock_path: str | None = None) -> None:
        self._conn = IpcConnection(sock_path).connect()
        with self._conn._lock:
            self._conn._send(MSG_SUBSCRIBE, json.dumps(["window"]))
            msg_type, reply = self._conn._recv(timeout=IPC_SUBSCRIBE_TIMEOUT)
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
        try:
            return self._queue.get(timeout=max(0.0, timeout))
        except Empty:
            return None

    def close(self) -> None:
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
    """Lazily-created process-wide command/query connection."""
    global _shared
    with _shared_lock:
        if _shared is None:
            _shared = IpcConnection().connect()
        return _shared


def close_connection() -> None:
    global _shared
    with _shared_lock:
        if _shared is not None:
            _shared.close()
            _shared = None


def run_command(cmd: str) -> list[dict]:
    """Run a sway command without raising on Sway failure."""
    return connection().command(cmd)


def run_command_logged(cmd: str) -> bool:
    """run_command + warn on failure. Returns True if all sub-commands ok."""
    result = run_command(cmd)
    bad = [r for r in result if not r.get("success", False)]
    if bad:
        log.warning("sway command failed: %s -> %s", cmd, bad)
        return False
    return True


def get_tree() -> dict[str, Any]:
    return connection().get_tree()


# Tree helpers


def walk_tree(node: dict) -> Iterator[dict]:
    yield node
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        yield from walk_tree(child)


def node_class(node: dict) -> str:
    props = node.get("window_properties") or {}
    return props.get("class") or node.get("class") or ""


def matches_app(node: dict, app_id: str, class_name: str) -> bool:
    n_app = node.get("app_id") or ""
    n_cls = node_class(node)

    # Prefer app_id when both sides expose one. A class match alone must not
    # allow an unrelated Wayland app_id to be claimed.
    if app_id:
        if n_app:
            return n_app == app_id
        return bool(class_name and n_cls == class_name)

    return bool(class_name and n_cls == class_name)


def is_window_node(node: dict) -> bool:
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
    return [
        n["id"]
        for n in walk_tree(tree)
        if n.get("type") in ("con", "floating_con")
        and matches_app(n, app_id, class_name)
        and n.get("id") is not None
    ]


def matching_window_ids(app_id: str, class_name: str) -> list[int]:
    return matching_window_ids_in_tree(get_tree(), app_id, class_name)
