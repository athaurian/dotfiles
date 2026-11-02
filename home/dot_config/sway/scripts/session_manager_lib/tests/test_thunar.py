"""Tests for Thunar state capture and restore."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.apps.generic as gen_mod
import session_manager_lib.apps.thunar as thunar_mod
from session_manager_lib.tests.helpers import FakeWatcher, RecordingPopen


class TestGetThunarInfo(unittest.TestCase):
    def test_returns_an_existing_directory_argument(self):
        with (
            tempfile.TemporaryDirectory() as first,
            tempfile.TemporaryDirectory() as second,
            unittest.mock.patch.object(
                thunar_mod, "read_cmdline", return_value=["thunar", first, second]
            ),
        ):
            self.assertEqual(thunar_mod.get_thunar_info(10), second)

    def test_ignores_flags_and_missing_directories(self):
        with (
            unittest.mock.patch.object(
                thunar_mod,
                "read_cmdline",
                return_value=["thunar", "--flag", "/no/such/dir"],
            ),
            unittest.mock.patch.object(Path, "readlink", side_effect=OSError),
        ):
            self.assertEqual(thunar_mod.get_thunar_info(10), "")

    def test_falls_back_to_the_process_working_directory(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            unittest.mock.patch.object(
                thunar_mod, "read_cmdline", return_value=["thunar"]
            ),
            unittest.mock.patch.object(Path, "readlink", return_value=Path(folder)),
        ):
            self.assertEqual(thunar_mod.get_thunar_info(10), folder)


class TestLaunchThunar(unittest.TestCase):
    def _launch(self, node, win_id=55):
        popen = RecordingPopen()
        claimed = set()
        with (
            unittest.mock.patch.object(thunar_mod.subprocess, "Popen", popen),
            unittest.mock.patch.object(thunar_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(
                gen_mod, "wait_for_window_by_pid", return_value=win_id
            ),
        ):
            result = thunar_mod.launch_thunar(node, claimed)
        return result, claimed, popen

    def test_launches_with_the_saved_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            result, claimed, popen = self._launch({"folder_path": folder})
        self.assertEqual(result, 55)
        self.assertEqual(claimed, {55})
        self.assertEqual(popen.commands, [["thunar", folder]])

    def test_falls_back_to_the_home_directory(self):
        with (
            tempfile.TemporaryDirectory() as home,
            unittest.mock.patch.object(Path, "home", return_value=Path(home)),
        ):
            result, claimed, popen = self._launch({"folder_path": "/no/such/dir"})
        self.assertEqual(result, 55)
        self.assertEqual(claimed, {55})
        self.assertEqual(popen.commands, [["thunar", home]])

    def test_returns_none_when_no_window_appears(self):
        result, claimed, _ = self._launch({}, win_id=None)
        self.assertIsNone(result)
        self.assertEqual(claimed, set())


if __name__ == "__main__":
    unittest.main()
