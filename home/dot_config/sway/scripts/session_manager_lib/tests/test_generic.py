"""Tests for the generic app launcher helpers."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

import session_manager_lib.apps.calibre as calibre_mod
import session_manager_lib.apps.generic as gen_mod
import session_manager_lib.apps.kitty as kitty_mod
import session_manager_lib.apps.mpv as mpv_mod
import session_manager_lib.apps.thunar as thunar_mod
import session_manager_lib.apps.zathura as zathura_mod
from session_manager_lib.tests.helpers import FakeWatcher, RecordingPopen


class TestGetCmdFromAppId(unittest.TestCase):
    def test_known_app_id_command(self):
        self.assertEqual(gen_mod.get_cmd_from_app_id("thunar", ""), ["thunar"])
        self.assertEqual(
            gen_mod.get_cmd_from_app_id("org.pwmt.zathura", ""), ["zathura"]
        )

    def test_kitty_returns_none(self):
        self.assertIsNone(gen_mod.get_cmd_from_app_id("kitty", ""))
        self.assertIsNone(gen_mod.get_cmd_from_app_id("kitty_drop", ""))

    def test_unknown_returns_empty(self):
        # Unknown app without desktop file returns empty sentinel (not None).
        self.assertEqual(gen_mod.get_cmd_from_app_id("", ""), [])
        self.assertEqual(gen_mod.get_cmd_from_app_id("no.such.app", ""), [])

    def test_gtk_launch_system_desktop(self):
        # Hermetic: patch exists to pretend thunar.desktop is present.
        with unittest.mock.patch.object(Path, "exists", return_value=True):
            self.assertEqual(
                gen_mod.get_cmd_from_app_id("", "thunar"), ["gtk-launch", "thunar"]
            )

    def test_gtk_launch_user_desktop(self):
        with tempfile.TemporaryDirectory() as tmp:
            user_apps = Path(tmp) / ".local" / "share" / "applications"
            user_apps.mkdir(parents=True)
            (user_apps / "sm_test_app.desktop").write_text(
                "[Desktop Entry]\n", encoding="utf-8"
            )
            with unittest.mock.patch.object(
                gen_mod.Path, "home", classmethod(lambda cls: Path(tmp))
            ):
                self.assertEqual(
                    gen_mod.get_cmd_from_app_id("", "sm_test_app"),
                    ["gtk-launch", "sm_test_app"],
                )


class TestWaitForWindowByPid(unittest.TestCase):
    def test_matches_new_event_by_pid(self):
        from types import SimpleNamespace

        events = iter(
            [
                SimpleNamespace(change="new", container={"pid": 555, "id": 91}),
            ]
        )

        class FakeWatcher:
            def get(self, timeout):
                return next(events, None)

        result = gen_mod.wait_for_window_by_pid(
            FakeWatcher(), 555, "kitty", timeout=0.2
        )
        self.assertEqual(result, 91)

    def test_ignores_other_pids_then_times_out(self):
        from types import SimpleNamespace

        events = iter([SimpleNamespace(change="new", container={"pid": 999, "id": 91})])

        class FakeWatcher:
            calls = 0

            def get(self, timeout):
                self.calls += 1
                # Return mismatched pid once, then timeout (None)
                if self.calls == 1:
                    return next(events, None)
                return None

        with unittest.mock.patch.object(
            gen_mod, "get_tree", return_value={"nodes": [], "floating_nodes": []}
        ):
            result = gen_mod.wait_for_window_by_pid(
                FakeWatcher(), 555, "kitty", timeout=0.05
            )
        self.assertIsNone(result)

    def test_falls_back_to_tree_scan(self):
        fake_tree = {
            "nodes": [
                {
                    "type": "con",
                    "id": 77,
                    "pid": 555,
                    "app_id": "kitty",
                    "nodes": [],
                    "floating_nodes": [],
                }
            ]
        }
        with unittest.mock.patch.object(gen_mod, "get_tree", return_value=fake_tree):
            result = gen_mod.wait_for_window_by_pid(
                unittest.mock.Mock(), 555, "kitty", timeout=0.01
            )
        self.assertEqual(result, 77)


def event(change, cid, app_id="kitty", container_type="con", timestamp=None):
    return SimpleNamespace(
        change=change,
        container={"id": cid, "app_id": app_id, "type": container_type},
        timestamp=float("inf") if timestamp is None else timestamp,
    )


class ScriptedWatcher:
    def __init__(self, events):
        self.events = list(events)

    def get(self, timeout):
        return self.events.pop(0) if self.events else None


class TestWaitForAppWindow(unittest.TestCase):
    def test_returns_a_matching_new_window(self):
        watcher = ScriptedWatcher([event("new", 7, timestamp=0)])
        self.assertEqual(
            gen_mod.wait_for_app_window("kitty", "", watcher, settle=0, timeout=0.2),
            7,
        )

    def test_ignores_baseline_and_claimed_windows(self):
        watcher = ScriptedWatcher(
            [
                event("new", 7, timestamp=0),
                event("new", 8, timestamp=0),
                event("new", 9, timestamp=0),
            ]
        )
        self.assertEqual(
            gen_mod.wait_for_app_window(
                "kitty",
                "",
                watcher,
                settle=0,
                timeout=0.2,
                baseline_ids={7},
                claimed_ids={8},
            ),
            9,
        )

    def test_close_event_removes_a_candidate(self):
        watcher = ScriptedWatcher([event("new", 7), event("close", 7)])
        with unittest.mock.patch.object(
            gen_mod, "find_unclaimed_window", return_value=None
        ) as fallback:
            result = gen_mod.wait_for_app_window(
                "kitty", "", watcher, settle=1, timeout=0.02
            )
        self.assertIsNone(result)
        fallback.assert_called_once()

    def test_rejects_a_floating_window(self):
        watcher = ScriptedWatcher([event("new", 7, container_type="floating_con")])
        with unittest.mock.patch.object(
            gen_mod, "find_unclaimed_window", return_value=None
        ):
            result = gen_mod.wait_for_app_window(
                "kitty",
                "",
                watcher,
                settle=0.1,
                timeout=0.02,
                reject_floating=True,
            )
        self.assertIsNone(result)

    def test_fails_fast_when_the_process_exits(self):
        process = unittest.mock.Mock()
        process.poll.return_value = 1
        with unittest.mock.patch.object(
            gen_mod, "find_unclaimed_window", return_value=None
        ):
            result = gen_mod.wait_for_app_window(
                "kitty",
                "",
                ScriptedWatcher([]),
                timeout=5,
                process=process,
                fail_fast_on_exit=True,
            )
        self.assertIsNone(result)

    def test_falls_back_to_a_tree_scan(self):
        with unittest.mock.patch.object(
            gen_mod, "find_unclaimed_window", return_value=9
        ):
            result = gen_mod.wait_for_app_window(
                "kitty", "", ScriptedWatcher([]), timeout=0.02
            )
        self.assertEqual(result, 9)


class TestLaunchDispatch(unittest.TestCase):
    def test_dedicated_launchers_are_used(self):
        cases = [
            ("kitty", kitty_mod, "launch_kitty"),
            ("kitty_drop", kitty_mod, "launch_kitty_drop"),
            ("zathura", zathura_mod, "launch_zathura"),
            ("calibre-ebook-viewer", calibre_mod, "launch_ebook_viewer"),
            ("thunar", thunar_mod, "launch_thunar"),
            ("mpv", mpv_mod, "launch_mpv"),
        ]
        for app_id, module, name in cases:
            with self.subTest(app_id=app_id):
                with unittest.mock.patch.object(
                    module, name, return_value=11
                ) as launcher:
                    result = gen_mod.launch_and_get_id(
                        {"app_id": app_id}, claimed_ids=set()
                    )
                self.assertEqual(result, 11)
                launcher.assert_called_once()

    def test_helium_is_restored_as_a_group(self):
        with unittest.mock.patch.object(gen_mod, "get_cmd_from_app_id") as get_cmd:
            self.assertIsNone(
                gen_mod.launch_and_get_id({"app_id": "helium"}, claimed_ids=set())
            )
        get_cmd.assert_not_called()

    def test_unknown_app_without_a_command_is_skipped(self):
        with unittest.mock.patch.object(
            gen_mod, "get_cmd_from_app_id", return_value=[]
        ):
            self.assertIsNone(
                gen_mod.launch_and_get_id({"app_id": "unknown"}, claimed_ids=set())
            )

    def test_generic_app_is_launched_and_claimed(self):
        popen = RecordingPopen()
        claimed = set()
        with (
            unittest.mock.patch.object(
                gen_mod, "get_cmd_from_app_id", return_value=["some-app"]
            ),
            unittest.mock.patch.object(gen_mod, "matching_window_ids", return_value=[]),
            unittest.mock.patch.object(gen_mod.subprocess, "Popen", popen),
            unittest.mock.patch.object(gen_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(gen_mod, "wait_for_app_window", return_value=12),
        ):
            result = gen_mod.launch_and_get_id({"app_id": "unknown"}, claimed)
        self.assertEqual(result, 12)
        self.assertEqual(claimed, {12})
        self.assertEqual(popen.commands, [["some-app"]])

    def test_singleton_app_is_not_launched_twice(self):
        with (
            unittest.mock.patch.object(
                gen_mod, "get_cmd_from_app_id", return_value=["vesktop"]
            ),
            unittest.mock.patch.object(
                gen_mod, "matching_window_ids", return_value=[5]
            ),
            unittest.mock.patch.object(gen_mod.subprocess, "Popen") as popen,
        ):
            self.assertIsNone(
                gen_mod.launch_and_get_id({"app_id": "vesktop"}, claimed_ids=set())
            )
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
