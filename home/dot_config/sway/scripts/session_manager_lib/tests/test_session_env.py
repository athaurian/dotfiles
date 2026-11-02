"""Tests for the compositor environment repair."""

import os
import unittest
import unittest.mock
from pathlib import Path

from session_manager_lib import session_env


def write_proc_tree(root, pid, comm, environ=None, sockets=None):
    """Builds a fake /proc tree for one process."""
    proc_dir = root / str(pid)
    proc_dir.mkdir(parents=True)
    (proc_dir / "comm").write_text(comm + "\n")
    env = environ or {}
    (proc_dir / "environ").write_bytes(
        b"".join(f"{k}={v}".encode() + b"\0" for k, v in env.items())
    )
    fd_dir = proc_dir / "fd"
    fd_dir.mkdir()
    for index, (inode, _path) in enumerate(sockets or []):
        os.symlink(f"socket:[{inode}]", fd_dir / str(index))
    net = root / "net"
    net.mkdir()
    lines = ["Num       RefCount Protocol Flags    Type St Inode Path"]
    for inode, path in sockets or []:
        lines.append(
            f"0000000000000000: 00000002 00000000 00010000 0001 01 {inode} {path}"
        )
    (net / "unix").write_text("\n".join(lines) + "\n")


class EnvTestCase(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._patch_proc = unittest.mock.patch.object(
            session_env, "PROC_ROOT", self.root
        )
        self._patch_proc.start()
        self.addCleanup(self._patch_proc.stop)
        self.addCleanup(self.tmp.cleanup)

    def patch_backend(self, backend):
        patch = unittest.mock.patch.object(
            session_env, "detect_backend", lambda: backend
        )
        patch.start()
        self.addCleanup(patch.stop)

    def patch_env(self, **values):
        patch = unittest.mock.patch.dict(os.environ, values, clear=True)
        patch.start()
        self.addCleanup(patch.stop)


class TestI3Environment(EnvTestCase):
    def test_display_comes_from_the_compositor(self):
        write_proc_tree(
            self.root,
            1234,
            "i3",
            environ={"DISPLAY": ":0", "XDG_RUNTIME_DIR": "/run/user/1000"},
        )
        self.patch_backend("i3")
        self.patch_env(PATH="/usr/bin")
        env = session_env.compositor_env()
        self.assertEqual(env["DISPLAY"], ":0")

    def test_existing_display_is_kept(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        self.patch_backend("i3")
        self.patch_env(DISPLAY=":7")
        self.assertEqual(session_env.compositor_env()["DISPLAY"], ":7")

    def test_empty_display_is_repaired(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        self.patch_backend("i3")
        self.patch_env(DISPLAY="")
        self.assertEqual(session_env.compositor_env()["DISPLAY"], ":0")

    def test_ipc_socket_is_exported(self):
        write_proc_tree(
            self.root,
            1234,
            "i3",
            sockets=[("111", "/run/user/1000/i3/ipc-socket.1234")],
        )
        self.patch_backend("i3")
        self.patch_env(PATH="/usr/bin")
        env = session_env.compositor_env()
        self.assertEqual(env["I3SOCK"], "/run/user/1000/i3/ipc-socket.1234")

    def test_xauthority_is_taken_from_the_compositor(self):
        write_proc_tree(
            self.root,
            1234,
            "i3",
            environ={"DISPLAY": ":0", "XAUTHORITY": "/run/user/1000/gdm/Xauthority"},
        )
        self.patch_backend("i3")
        self.patch_env(PATH="/usr/bin")
        env = session_env.compositor_env()
        self.assertEqual(env["XAUTHORITY"], "/run/user/1000/gdm/Xauthority")

    def test_missing_compositor_changes_nothing(self):
        self.patch_backend("i3")
        self.patch_env(PATH="/usr/bin")
        self.assertEqual(session_env.compositor_env(), {"PATH": "/usr/bin"})


class TestSwayEnvironment(EnvTestCase):
    def test_wayland_display_comes_from_the_open_socket(self):
        write_proc_tree(
            self.root,
            4321,
            "sway",
            environ={"XDG_RUNTIME_DIR": "/run/user/1000"},
            sockets=[
                ("111", "/run/user/1000/sway-ipc.1000.4321.sock"),
                ("222", "/run/user/1000/wayland-1"),
            ],
        )
        self.patch_backend("sway")
        self.patch_env(PATH="/usr/bin")
        env = session_env.compositor_env()
        self.assertEqual(env["WAYLAND_DISPLAY"], "wayland-1")
        self.assertEqual(env["XDG_RUNTIME_DIR"], "/run/user/1000")

    def test_existing_wayland_display_is_kept(self):
        write_proc_tree(
            self.root,
            4321,
            "sway",
            sockets=[("222", "/run/user/1000/wayland-1")],
        )
        self.patch_backend("sway")
        self.patch_env(WAYLAND_DISPLAY="wayland-9")
        self.assertEqual(session_env.compositor_env()["WAYLAND_DISPLAY"], "wayland-9")

    def test_runtime_dir_is_recovered_without_a_wayland_socket(self):
        write_proc_tree(
            self.root,
            4321,
            "sway",
            environ={"XDG_RUNTIME_DIR": "/run/user/1000"},
        )
        self.patch_backend("sway")
        self.patch_env(WAYLAND_DISPLAY="wayland-1")
        env = session_env.compositor_env()
        self.assertEqual(env["XDG_RUNTIME_DIR"], "/run/user/1000")

    def test_ipc_socket_is_exported(self):
        write_proc_tree(
            self.root,
            4321,
            "sway",
            sockets=[("111", "/run/user/1000/sway-ipc.1000.4321.sock")],
        )
        self.patch_backend("sway")
        self.patch_env(PATH="/usr/bin")
        env = session_env.compositor_env()
        self.assertEqual(env["SWAYSOCK"], "/run/user/1000/sway-ipc.1000.4321.sock")


class TestApplyEnv(EnvTestCase):
    def test_apply_writes_missing_variables(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        self.patch_backend("i3")
        self.patch_env(PATH="/usr/bin")
        self.assertTrue(session_env.apply_compositor_env())
        self.assertEqual(os.environ["DISPLAY"], ":0")

    def test_apply_repairs_an_empty_variable(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        self.patch_backend("i3")
        self.patch_env(DISPLAY="")
        self.assertTrue(session_env.apply_compositor_env())
        self.assertEqual(os.environ["DISPLAY"], ":0")

    def test_apply_reports_no_change_when_nothing_is_missing(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        self.patch_backend("i3")
        self.patch_env(DISPLAY=":0")
        self.assertFalse(session_env.apply_compositor_env())


class TestParsing(EnvTestCase):
    def test_read_environ_handles_entries_without_a_value(self):
        write_proc_tree(self.root, 1234, "i3", environ={"DISPLAY": ":0"})
        (self.root / "1234" / "environ").write_bytes(b"DISPLAY=:0\0BROKEN\0")
        env = session_env._read_environ(1234)
        self.assertEqual(env, {"DISPLAY": ":0"})

    def test_socket_paths_ignore_unrelated_inodes(self):
        write_proc_tree(
            self.root,
            1234,
            "i3",
            sockets=[("222", "/run/user/1000/i3/ipc-socket.1234")],
        )
        paths = session_env._socket_paths(1234)
        self.assertEqual(paths, ["/run/user/1000/i3/ipc-socket.1234"])

    def test_missing_process_is_handled(self):
        self.assertEqual(session_env._read_environ(999999), {})
        self.assertEqual(session_env._socket_paths(999999), [])
        self.assertEqual(session_env._find_pids("i3"), [])
