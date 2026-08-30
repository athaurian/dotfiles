"""Tests for the generic app launcher helpers."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.apps.generic as gen_mod


class TestGetCmdFromAppId(unittest.TestCase):
    def test_known_app_id_command(self):
        self.assertEqual(gen_mod.get_cmd_from_app_id("thunar", ""), ["thunar"])
        self.assertEqual(
            gen_mod.get_cmd_from_app_id("org.pwmt.zathura", ""), ["zathura"]
        )

    def test_foot_returns_none(self):
        self.assertIsNone(gen_mod.get_cmd_from_app_id("foot", ""))
        self.assertIsNone(gen_mod.get_cmd_from_app_id("foot_drop", ""))

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

        result = gen_mod.wait_for_window_by_pid(FakeWatcher(), 555, "foot", timeout=0.2)
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
                FakeWatcher(), 555, "foot", timeout=0.05
            )
        self.assertIsNone(result)

    def test_falls_back_to_tree_scan(self):
        fake_tree = {
            "nodes": [
                {
                    "type": "con",
                    "id": 77,
                    "pid": 555,
                    "app_id": "foot",
                    "nodes": [],
                    "floating_nodes": [],
                }
            ]
        }
        with unittest.mock.patch.object(gen_mod, "get_tree", return_value=fake_tree):
            result = gen_mod.wait_for_window_by_pid(
                unittest.mock.Mock(), 555, "foot", timeout=0.01
            )
        self.assertEqual(result, 77)


if __name__ == "__main__":
    unittest.main()
