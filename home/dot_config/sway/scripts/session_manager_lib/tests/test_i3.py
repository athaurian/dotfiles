"""Tests for i3 support: X11 identities, floats, sockets, and state paths."""

import os
import unittest
import unittest.mock

import session_manager_lib.apps.generic as gen_mod
import session_manager_lib.background as bg_mod
import session_manager_lib.config as cfg_mod
import session_manager_lib.ipc as ipc_mod
import session_manager_lib.sway_tree as st_mod
from session_manager_lib.tests.helpers import (
    RestoreHarnessTestCase,
    make_window,
    make_workspace,
)


class FakeCache:
    def __init__(self, cwd="/home/user/proj", nvim_pid=None):
        self.cwd = cwd
        self.nvim_pid = nvim_pid

    def get_terminal_cwd(self, pid):
        return self.cwd

    def get_nvim_pid(self, pid):
        return self.nvim_pid

    def get_zellij_session(self, pid):
        return None

    def is_ssh_or_sudo(self, pid):
        return False, ""


def i3_window(class_name, instance=None, **extra):
    """A tiled window as i3 reports it (WM_CLASS, no app_id)."""
    node = {
        "type": "con",
        "name": f"{class_name} window",
        "pid": 12345,
        "window": 987654,
        "fullscreen_mode": 0,
        "rect": {"x": 0, "y": 0, "width": 800, "height": 600},
        "marks": [],
        "scratchpad_state": "none",
        "nodes": [],
        "floating_nodes": [],
        "window_properties": {"class": class_name, "instance": instance or class_name},
    }
    node.update(extra)
    return node


def i3_float(child, **extra):
    """An i3 floating_con wrapper around one window child."""
    wrapper = {
        "type": "floating_con",
        "name": None,
        "pid": None,
        "window": None,
        "rect": {"x": 100, "y": 120, "width": 640, "height": 480},
        "marks": [],
        "scratchpad_state": "none",
        "fullscreen_mode": 0,
        "nodes": [child],
        "floating_nodes": [],
    }
    wrapper.update(extra)
    return wrapper


class TestBackendDetection(unittest.TestCase):
    def test_explicit_override(self):
        with unittest.mock.patch.dict(
            os.environ, {"SESSION_MANAGER_BACKEND": "i3"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "i3")
        with unittest.mock.patch.dict(
            os.environ, {"SESSION_MANAGER_BACKEND": "sway"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "sway")

    def test_socket_environment_decides(self):
        with unittest.mock.patch.dict(
            os.environ, {"I3SOCK": "/run/i3.sock"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "i3")
        with unittest.mock.patch.dict(
            os.environ, {"SWAYSOCK": "/run/sway.sock"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "sway")

    def test_desktop_name_fallback(self):
        with unittest.mock.patch.dict(
            os.environ, {"XDG_CURRENT_DESKTOP": "i3"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "i3")
        with unittest.mock.patch.dict(
            os.environ, {"XDG_CURRENT_DESKTOP": "sway"}, clear=True
        ):
            self.assertEqual(cfg_mod.detect_backend(), "sway")

    def test_state_files_are_separate(self):
        self.assertEqual(cfg_mod.I3_STATE_FILE.name, "i3_session.json")
        self.assertEqual(cfg_mod.SWAY_STATE_FILE.name, "sway_session.json")
        self.assertNotEqual(cfg_mod.I3_STATE_FILE, cfg_mod.SWAY_STATE_FILE)
        self.assertEqual(
            cfg_mod.I3_BACKGROUND_APPS_FILE.name,
            "i3_session_background_apps.json",
        )
        self.assertEqual(
            cfg_mod.SWAY_BACKGROUND_APPS_FILE.name,
            "sway_session_background_apps.json",
        )
        self.assertNotEqual(
            cfg_mod.I3_BACKGROUND_APPS_FILE, cfg_mod.SWAY_BACKGROUND_APPS_FILE
        )

    def test_lock_file_is_scoped_to_the_backend(self):
        # An i3 and a Sway session must not serialise against each other.
        self.assertIn(cfg_mod.BACKEND, ("i3", "sway"))
        self.assertEqual(cfg_mod.LOCK_FILE_NAME, f"{cfg_mod.BACKEND}_session.lock")

    def test_active_paths_follow_the_backend(self):
        # Whichever backend is detected decides which file the CLI touches.
        self.assertEqual(
            cfg_mod.STATE_FILE.name,
            f"{cfg_mod.BACKEND}_session.json",
        )
        self.assertEqual(
            cfg_mod.BACKGROUND_APPS_FILE.name,
            f"{cfg_mod.BACKEND}_session_background_apps.json",
        )


class TestSocketResolution(unittest.TestCase):
    """Socket resolution only accepts paths that are live socket files."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.i3_sock = self._socket("i3.sock")
        self.sway_sock = self._socket("sway.sock")

    def _socket(self, name):
        import socket

        path = os.path.join(self.tmp.name, name)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(path)
        sock.close()
        return path

    def test_i3_socket_environment(self):
        with unittest.mock.patch.dict(os.environ, {"I3SOCK": self.i3_sock}, clear=True):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.i3_sock)

    def test_sway_socket_environment(self):
        with unittest.mock.patch.dict(
            os.environ, {"SWAYSOCK": self.sway_sock}, clear=True
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.sway_sock)

    def test_explicit_socket_override_wins(self):
        env = {
            "I3SOCK": self.i3_sock,
            "SWAYSOCK": self.sway_sock,
            "SESSION_MANAGER_SOCK": "/run/explicit.sock",
        }
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(ipc_mod.resolve_socket_path(), "/run/explicit.sock")

    def test_backend_selects_the_matching_socket(self):
        env = {"I3SOCK": self.i3_sock, "SWAYSOCK": self.sway_sock}
        with unittest.mock.patch.dict(
            os.environ, {**env, "SESSION_MANAGER_BACKEND": "i3"}, clear=True
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.i3_sock)
        with unittest.mock.patch.dict(
            os.environ, {**env, "SESSION_MANAGER_BACKEND": "sway"}, clear=True
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.sway_sock)

    def test_falls_back_to_get_socketpath(self):
        with (
            unittest.mock.patch.dict(
                os.environ, {"SESSION_MANAGER_BACKEND": "i3"}, clear=True
            ),
            unittest.mock.patch.object(
                ipc_mod,
                "_socket_from_binary",
                side_effect=lambda backend: self.i3_sock if backend == "i3" else "",
            ),
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.i3_sock)

    def test_stale_socket_is_skipped(self):
        """A socket path left over from a previous run must not be used."""
        stale = os.path.join(self.tmp.name, "gone.sock")
        with (
            unittest.mock.patch.dict(
                os.environ,
                {"I3SOCK": stale, "SESSION_MANAGER_BACKEND": "i3"},
                clear=True,
            ),
            unittest.mock.patch.object(
                ipc_mod,
                "_socket_from_binary",
                side_effect=lambda backend: self.i3_sock if backend == "i3" else "",
            ),
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), self.i3_sock)

    def test_no_live_socket_returns_empty(self):
        with (
            unittest.mock.patch.dict(
                os.environ,
                {"I3SOCK": os.path.join(self.tmp.name, "gone.sock")},
                clear=True,
            ),
            unittest.mock.patch.object(ipc_mod, "_socket_from_binary", return_value=""),
        ):
            self.assertEqual(ipc_mod.resolve_socket_path(), "")


class TestAppIdentity(unittest.TestCase):
    def test_canonical_aliases(self):
        self.assertEqual(cfg_mod.canonical_app_id("Thunar"), "thunar")
        self.assertEqual(cfg_mod.canonical_app_id("Zathura"), "org.pwmt.zathura")
        self.assertEqual(cfg_mod.canonical_app_id("Helium"), "helium")
        self.assertEqual(
            cfg_mod.canonical_app_id("KeePassXC"), "org.keepassxc.KeePassXC"
        )

    def test_i3_class_is_the_app_id(self):
        node = i3_window("Thunar")
        self.assertEqual(ipc_mod.node_app_id(node), "thunar")
        self.assertTrue(ipc_mod.matches_app(node, "thunar", "Thunar"))
        self.assertFalse(ipc_mod.matches_app(node, "kitty", "Thunar"))

    def test_instance_is_available_for_drop_terminals(self):
        node = i3_window("kitty", instance="scratchpad_term")
        self.assertEqual(ipc_mod.node_app_id(node), "kitty")
        self.assertEqual(ipc_mod.node_instance(node), "scratchpad_term")


class TestCleanTreeI3(unittest.TestCase):
    def test_x11_window_uses_class_as_app_id(self):
        node = i3_window("Thunar", border="normal")
        with unittest.mock.patch.object(
            st_mod, "get_thunar_info", return_value="/home/user"
        ):
            result = st_mod.clean_tree(node, FakeCache())
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "window")
        self.assertEqual(result["app_id"], "thunar")
        self.assertEqual(result["class"], "Thunar")
        self.assertEqual(result["folder_path"], "/home/user")
        self.assertEqual(result["border"], "normal")

    def test_helium_class_is_restorable(self):
        result = st_mod.clean_tree(i3_window("Helium"), FakeCache())
        self.assertEqual(result["app_id"], "helium")

    def test_topgrade_instance_is_transient(self):
        node = i3_window("kitty", instance="topgrade_term")
        self.assertIsNone(st_mod.clean_tree(node, FakeCache()))

    def test_topgrade_mark_is_transient(self):
        node = i3_window("kitty", marks=["topgrade_term"])
        self.assertIsNone(st_mod.clean_tree(node, FakeCache()))

    def test_drop_terminal_instance_is_classified(self):
        node = i3_window("kitty", instance="scratchpad_term")
        result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["app_id"], "kitty_drop")

    def test_drop_terminal_mark_is_classified(self):
        node = i3_window("kitty", marks=["drop_term"])
        result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["app_id"], "kitty_drop")

    def test_floating_wrapper_is_unwrapped(self):
        child = i3_window("kitty")
        wrapper = i3_float(child, marks=["floating-mark"], scratchpad_state="changed")
        result = st_mod.clean_tree(wrapper, FakeCache())
        self.assertIsNotNone(result)
        self.assertEqual(result["app_id"], "kitty")
        self.assertEqual(result["scratchpad_state"], "changed")
        self.assertEqual(
            result["rect"], {"x": 100, "y": 120, "width": 640, "height": 480}
        )
        self.assertIn("floating-mark", result["marks"])

    def test_plain_float_is_not_in_the_scratchpad(self):
        """A normal floating window must not be saved as a scratchpad one."""
        child = i3_window("kitty")
        result = st_mod.clean_tree(i3_float(child), FakeCache())
        self.assertIsNotNone(result)
        self.assertEqual(result["scratchpad_state"], "none")

    def test_floating_group_in_a_workspace_keeps_every_window(self):
        """A floating group holds several windows; none of them may vanish."""
        inner = {
            "type": "con",
            "layout": "tabbed",
            "nodes": [
                i3_window("kitty", name="first"),
                i3_window("Helium", name="second"),
            ],
            "floating_nodes": [],
        }
        group = i3_float(inner, nodes=[inner])
        ws = {
            "type": "workspace",
            "name": "1",
            "layout": "splith",
            "nodes": [],
            "floating_nodes": [group],
        }
        result = st_mod.clean_tree(ws, FakeCache())
        self.assertEqual(len(result["floating_nodes"]), 2)
        self.assertEqual(
            [w["app_id"] for w in result["floating_nodes"]], ["kitty", "helium"]
        )

    def test_floating_group_children_are_kept(self):
        """The windows of a floating group are saved separately."""
        inner = {
            "type": "con",
            "layout": "tabbed",
            "nodes": [
                i3_window("kitty", name="first"),
                i3_window("Helium", name="second"),
            ],
            "floating_nodes": [],
        }
        group = i3_float(inner, nodes=[inner])
        windows = st_mod.clean_floating(group, FakeCache())
        self.assertEqual([w["app_id"] for w in windows], ["kitty", "helium"])

    def test_floating_wrapper_keeps_child_marks(self):
        child = i3_window("kitty", marks=["child-mark"])
        wrapper = i3_float(child, marks=["wrapper-mark"])
        result = st_mod.clean_tree(wrapper, FakeCache())
        self.assertEqual(result["marks"], ["wrapper-mark", "child-mark"])

    def test_floating_wrapper_transient_child_is_skipped(self):
        child = i3_window("kitty", instance="topgrade_term")
        self.assertIsNone(st_mod.clean_tree(i3_float(child), FakeCache()))

    def test_nested_workspace_keeps_children(self):
        child = i3_window("Helium")
        ws = {
            "type": "workspace",
            "name": "1",
            "layout": "splith",
            "nodes": [child],
            "floating_nodes": [i3_float(i3_window("kitty"))],
        }
        result = st_mod.clean_tree(ws, FakeCache())
        self.assertEqual(result["type"], "workspace")
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(len(result["floating_nodes"]), 1)


class TestI3WindowLookup(unittest.TestCase):
    def test_fallback_tree_scan_matches_wm_class(self):
        fake_tree = {
            "nodes": [
                {
                    "type": "con",
                    "id": 77,
                    "pid": 555,
                    "name": "file manager",
                    "window": 999,
                    "window_properties": {"class": "Thunar"},
                    "nodes": [],
                    "floating_nodes": [],
                }
            ]
        }
        with unittest.mock.patch.object(gen_mod, "get_tree", return_value=fake_tree):
            result = gen_mod.wait_for_window_by_pid(
                unittest.mock.Mock(), 555, "thunar", timeout=0.01
            )
        self.assertEqual(result, 77)


class TestI3Geometry(RestoreHarnessTestCase):
    backend = "i3"

    def test_i3_uses_output_absolute_coords_without_titlebar_offset(self):
        self.restore_mod._apply_geometry(
            1000, {"x": 243, "y": 197, "width": 800, "height": 600}, "1"
        )
        self.assertCommand("move position 243 197")
        self.assertCommand("resize set width 800 px height 600 px")

    def test_i3_geometry_is_applied_once(self):
        """i3 applies geometry directly, so no settle-and-retry is needed."""
        self.restore_mod._apply_geometry(
            1000, {"x": 243, "y": 197, "width": 800, "height": 600}, "1"
        )
        self.assertEqual(len([c for c in self.calls if "resize set" in c]), 1)
        self.assertEqual(len([c for c in self.calls if "move position" in c]), 1)

    def test_i3_does_not_stage_on_internal_scratch_workspace(self):
        self.restore_mod._restore_hidden_scratchpad(
            make_window("kitty", marks=["s"]), self.restore_mod.RestoreContext()
        )
        self.assertNotIn("workspace __scratch_restore", " ".join(self.calls))


class TestI3Restore(RestoreHarnessTestCase):
    backend = "i3"

    def test_hidden_drop_terminal_restores_its_mark(self):
        payload = {
            "workspaces": [],
            "hidden_scratchpad": [make_window("kitty_drop", marks=["drop_term"])],
            "background_apps": [],
        }
        self.restore_workspaces(payload)
        self.assertCommand("mark drop_term")
        self.assertCommand("move scratchpad")

    def test_x11_saved_window_restores_by_class(self):
        win = make_window("thunar", name="file manager")
        win["class"] = "Thunar"
        ws = make_workspace("1", nodes=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("[con_id=1000] focus")

    def test_workspace_names_with_spaces_are_quoted(self):
        ws = make_workspace("1: web", nodes=[make_window("kitty")])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand('workspace "1: web"')

    def test_hidden_plain_window_restores_saved_border(self):
        payload = {
            "workspaces": [],
            "hidden_scratchpad": [make_window("kitty", name="keep", border="pixel")],
            "background_apps": [],
        }
        self.restore_workspaces(payload)
        self.assertCommand("[con_id=1000] border pixel")
        self.assertCommand("move scratchpad")

    def test_hidden_plain_window_without_border_defaults_to_normal(self):
        payload = {
            "workspaces": [],
            "hidden_scratchpad": [make_window("kitty", name="keep")],
            "background_apps": [],
        }
        payload["hidden_scratchpad"][0].pop("border", None)
        self.restore_workspaces(payload)
        self.assertCommand("[con_id=1000] border normal")

    def test_floating_window_restores_saved_border(self):
        ws = make_workspace("1", floating=[make_window("kitty", border="none")])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("[con_id=1000] border none")

    def test_floating_window_border_none_is_not_applied_when_absent(self):
        ws = make_workspace("1", floating=[make_window("kitty")])
        payload = {"workspaces": [ws]}
        payload["workspaces"][0]["floating_nodes"][0].pop("border", None)
        self.restore_workspaces(payload)
        self.assertNotIn("border", " ".join(self.calls))

    def test_clamped_rect_stays_absolute_on_i3(self):
        self.restore_workspaces(
            {
                "workspaces": [
                    make_workspace(
                        "1",
                        floating=[
                            make_window(
                                "kitty",
                                rect={
                                    "x": -500,
                                    "y": 4000,
                                    "width": 200,
                                    "height": 100,
                                },
                            )
                        ],
                    )
                ]
            }
        )
        moves = [c for c in self.calls if "move position" in c]
        self.assertEqual(moves, ["[con_id=1000] move position 0 980"], moves)


class TestBackgroundTarget(unittest.TestCase):
    def test_i3_uses_i3_session_target(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return unittest.mock.Mock(returncode=0, stdout="")

        with (
            unittest.mock.patch.object(bg_mod, "detect_backend", return_value="i3"),
            unittest.mock.patch.object(bg_mod.subprocess, "run", fake_run),
            unittest.mock.patch(
                "session_manager_lib.logging_setup.notify", lambda *a, **kw: None
            ),
        ):
            bg_mod._ensure_background_daemons()

        self.assertIn(
            ["systemctl", "--user", "is-active", "--quiet", "i3-session.target"],
            calls,
        )
        self.assertFalse(
            any("sway-session.target" in part for call in calls for part in call)
        )


class TestX11PidRecovery(unittest.TestCase):
    """i3's tree omits the pid, so the X11 tools fill it in."""

    def _result(self, stdout="", returncode=0):
        import subprocess

        return subprocess.CompletedProcess(
            args=[], returncode=returncode, stdout=stdout, stderr=""
        )

    def test_xdotool_pid_is_used(self):
        with unittest.mock.patch.object(
            ipc_mod.subprocess, "run", return_value=self._result("4242\n")
        ) as run:
            self.assertEqual(ipc_mod.node_pid({"window": 987654}), 4242)
        self.assertEqual(run.call_args[0][0][:2], ["xdotool", "getwindowpid"])

    def test_xprop_is_the_fallback(self):
        def fake_run(cmd, **_kwargs):
            if cmd[0] == "xdotool":
                return self._result("", returncode=1)
            return self._result("_NET_WM_PID = 5150\n")

        with unittest.mock.patch.object(
            ipc_mod.subprocess, "run", side_effect=fake_run
        ):
            self.assertEqual(ipc_mod.node_pid({"window": 987654}), 5150)

    def test_no_pid_when_both_tools_fail(self):
        with unittest.mock.patch.object(
            ipc_mod.subprocess, "run", return_value=self._result("", returncode=1)
        ):
            self.assertEqual(ipc_mod.node_pid({"window": 987654}), 0)

    def test_tree_pid_wins(self):
        self.assertEqual(ipc_mod.node_pid({"pid": 99, "window": 1}), 99)


if __name__ == "__main__":
    unittest.main()
