"""Tests for Neovim runtime socket and snapshot path discovery."""

import os
import socket
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.config as cfg_mod
from session_manager_lib.nvim.snapshot import get_nvim_snapshot_path
from session_manager_lib.nvim.sockets import (
    nvim_socket_path,
    runtime_dir,
    runtime_nvim_sockets,
    sock_pid,
)


class TestRuntimeDir(unittest.TestCase):
    def test_uses_environment_value(self):
        with unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/tmp/run"}):
            self.assertEqual(runtime_dir(), Path("/tmp/run"))

    def test_falls_back_to_user_run_directory(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(runtime_dir(), Path(f"/run/user/{os.getuid()}"))


class TestSocketPaths(unittest.TestCase):
    def test_socket_path_uses_runtime_dir(self):
        with unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/tmp/run"}):
            self.assertEqual(nvim_socket_path(1234), Path("/tmp/run/nvim.1234.0"))

    def test_sock_pid_parses_socket_name(self):
        self.assertEqual(sock_pid(Path("/run/user/1000/nvim.4321.0")), 4321)

    def test_sock_pid_rejects_unparseable_names(self):
        self.assertIsNone(sock_pid(Path("/run/user/1000/nvim.sock")))
        self.assertIsNone(sock_pid(Path("/run/user/1000/nvim")))

    def test_runtime_sockets_ignore_regular_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.addCleanup(server.close)
            sock_path = Path(tmp) / "nvim.99.0"
            server.bind(str(sock_path))
            (Path(tmp) / "nvim.100.0").write_text("", encoding="utf-8")
            with unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": tmp}):
                self.assertEqual(runtime_nvim_sockets(), [sock_path])


class TestSnapshotPath(unittest.TestCase):
    def test_snapshot_path_escapes_cwd_and_appends_pid(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            unittest.mock.patch.object(cfg_mod, "STATE_DIR", Path(tmp)),
        ):
            path = get_nvim_snapshot_path("/home/user/proj", pid=42)
            self.assertIn("%home%user%proj%42", str(path))
            self.assertTrue(str(path).endswith(".vim"))


if __name__ == "__main__":
    unittest.main()
