"""Tests for the IPC connection's failure handling.

A broken connection must never leave a half-read reply behind: the next
command would then read the previous answer.
"""

import json
import os
import socket
import tempfile
import threading
import unittest
import unittest.mock

from session_manager_lib import ipc as ipc_mod
from session_manager_lib.ipc import (
    EVENT_BIT,
    EVENT_WINDOW,
    HEADER,
    MAGIC,
    MSG_GET_TREE,
    MSG_SUBSCRIBE,
    IpcConnection,
    IpcError,
    WindowEventWatcher,
)


class FakeCompositor:
    """A unix socket that accepts a connection and can reply or stay quiet."""

    def __init__(self, tmpdir):
        self.path = os.path.join(tmpdir, "ipc.sock")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.path)
        self.sock.listen(1)
        self.conn: socket.socket | None = None

    def accept(self):
        self.conn, _ = self.sock.accept()

    def send(self, payload: bytes):
        assert self.conn is not None
        self.conn.sendall(payload)

    def send_reply(self, text: str):
        self.send_message(0, text)

    def send_message(self, msg_type: int, text: str):
        body = text.encode()
        self.send(HEADER.pack(MAGIC, len(body), msg_type) + body)

    def close(self):
        if self.conn is not None:
            self.conn.close()
        self.sock.close()


class TestConnectionFailures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = FakeCompositor(self.tmp.name)
        self.addCleanup(self.server.close)
        shared = unittest.mock.patch.object(ipc_mod, "_shared", None)
        shared.start()
        self.addCleanup(shared.stop)

    def _connect(self):
        conn = IpcConnection(sock_path=self.server.path).connect()
        self.addCleanup(conn.close)
        return conn

    def test_command_timeout_closes_the_connection(self):
        conn = self._connect()
        self.server.accept()
        with self.assertRaises(TimeoutError):
            conn.command("get_tree", timeout=0.2)
        # The socket is dropped so the next command starts fresh.
        self.assertIsNone(conn._sock)

    def test_partial_reply_is_a_fatal_error(self):
        conn = self._connect()
        self.server.accept()
        # Half a header, then silence: the stream is out of step.
        self.server.send(HEADER.pack(MAGIC, 32, 0)[:6])
        with self.assertRaises(IpcError):
            conn.command("get_tree", timeout=0.2)
        self.assertIsNone(conn._sock)

    def test_connecting_to_a_missing_socket_raises_ipc_error(self):
        with self.assertRaises(IpcError):
            IpcConnection(sock_path=os.path.join(self.tmp.name, "gone")).connect()

    def test_ipc_error_is_an_oserror(self):
        """Callers guard IPC calls with `except OSError`, so it must be one.

        An unreachable socket is an I/O failure, and the guards around
        get_tree() and run_command() rely on that.
        """
        self.assertTrue(issubclass(IpcError, OSError))
        with self.assertRaises(OSError):
            IpcConnection(sock_path=os.path.join(self.tmp.name, "gone")).connect()

    def test_shared_connection_is_rebuilt_after_a_failure(self):
        conn = self._connect()
        conn.close()

        class FakeConnection:
            def connect(self):
                return self

            def close(self):
                pass

        with unittest.mock.patch.object(ipc_mod, "IpcConnection", FakeConnection):
            rebuilt = ipc_mod.connection()
        self.assertIsInstance(rebuilt, FakeConnection)
        ipc_mod.close_connection()

    def test_command_after_a_timeout_reads_the_new_reply(self):
        """The connection is rebuilt, so no stale reply can be returned."""
        conn = self._connect()
        self.server.accept()
        with self.assertRaises(TimeoutError):
            conn.command("first", timeout=0.2)
        self.assertIsNone(conn._sock)


class TestRequests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = FakeCompositor(self.tmp.name)
        self.addCleanup(self.server.close)

    def _connect(self):
        conn = IpcConnection(sock_path=self.server.path).connect()
        self.addCleanup(conn.close)
        self.server.accept()
        return conn

    def test_get_tree_returns_the_payload(self):
        conn = self._connect()
        payload = {"nodes": []}
        self.server.send_message(MSG_GET_TREE, json.dumps(payload))
        self.assertEqual(conn.get_tree(), payload)

    def test_get_tree_rejects_a_command_reply(self):
        conn = self._connect()
        self.server.send_message(0, "[]")
        with self.assertRaises(IpcError):
            conn.get_tree()

    def test_command_checked_rejects_a_failed_subcommand(self):
        conn = IpcConnection(sock_path=self.server.path)
        with (
            unittest.mock.patch.object(
                conn,
                "command",
                return_value=[{"success": True}, {"success": False}],
            ),
            self.assertRaises(IpcError),
        ):
            conn.command_checked("split h")

    def test_command_checked_returns_successful_results(self):
        conn = IpcConnection(sock_path=self.server.path)
        results = [{"success": True}]
        with unittest.mock.patch.object(conn, "command", return_value=results):
            self.assertEqual(conn.command_checked("split h"), results)


class TestWindowEventWatcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = FakeCompositor(self.tmp.name)
        self.addCleanup(self.server.close)

    def _serve(self, subscribe_reply, event=None):
        def serve():
            self.server.accept()
            self.server.send_message(MSG_SUBSCRIBE, subscribe_reply)
            if event is not None:
                self.server.send_message(EVENT_BIT | EVENT_WINDOW, json.dumps(event))

        thread = threading.Thread(target=serve)
        thread.start()
        return thread

    def test_receives_a_window_event(self):
        thread = self._serve(
            '{"success": true}',
            {"change": "new", "container": {"id": 7, "app_id": "kitty"}},
        )
        watcher = WindowEventWatcher(self.server.path)
        self.addCleanup(watcher.close)
        event = watcher.get(timeout=1.0)
        thread.join(timeout=1.0)
        self.assertIsNotNone(event)
        self.assertEqual(event.change, "new")
        self.assertEqual(event.container["id"], 7)

    def test_rejected_subscription_raises(self):
        thread = self._serve('{"success": false}')
        with self.assertRaises(IpcError):
            WindowEventWatcher(self.server.path)
        thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
