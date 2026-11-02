"""Tests for mpv state capture and restore."""

import tempfile
import unittest
import unittest.mock

import session_manager_lib.apps.generic as gen_mod
import session_manager_lib.apps.mpv as mpv_mod
from session_manager_lib.tests.helpers import FakeWatcher, RecordingPopen


class TestGetMpvInfo(unittest.TestCase):
    def test_returns_an_existing_media_argument(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".mkv") as media,
            unittest.mock.patch.object(
                mpv_mod, "read_cmdline", return_value=["mpv", "--flag", media.name]
            ),
        ):
            self.assertEqual(mpv_mod.get_mpv_info(10), media.name)

    def test_ignores_missing_files_and_flags(self):
        with unittest.mock.patch.object(
            mpv_mod, "read_cmdline", return_value=["mpv", "--flag", "/no/such/file"]
        ):
            self.assertEqual(mpv_mod.get_mpv_info(10), "")

    def test_returns_empty_without_a_command_line(self):
        with unittest.mock.patch.object(mpv_mod, "read_cmdline", return_value=[]):
            self.assertEqual(mpv_mod.get_mpv_info(10), "")


class TestLaunchMpv(unittest.TestCase):
    def test_missing_media_does_not_launch(self):
        popen = RecordingPopen()
        with unittest.mock.patch.object(mpv_mod.subprocess, "Popen", popen):
            self.assertIsNone(
                mpv_mod.launch_mpv({"media_path": "/no/such/file"}, set())
            )
        self.assertEqual(popen.commands, [])

    def test_launches_with_force_window_and_claims_the_window(self):
        popen = RecordingPopen()
        claimed = set()
        with (
            tempfile.NamedTemporaryFile(suffix=".mkv") as media,
            unittest.mock.patch.object(mpv_mod.subprocess, "Popen", popen),
            unittest.mock.patch.object(mpv_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(
                gen_mod, "wait_for_window_by_pid", return_value=77
            ),
        ):
            win_id = mpv_mod.launch_mpv({"media_path": media.name}, claimed)
        self.assertEqual(win_id, 77)
        self.assertEqual(claimed, {77})
        self.assertEqual(popen.commands, [["mpv", "--force-window", media.name]])

    def test_returns_none_when_no_window_appears(self):
        claimed = set()
        with (
            tempfile.NamedTemporaryFile(suffix=".mkv") as media,
            unittest.mock.patch.object(mpv_mod.subprocess, "Popen", RecordingPopen()),
            unittest.mock.patch.object(mpv_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(
                gen_mod, "wait_for_window_by_pid", return_value=None
            ),
        ):
            win_id = mpv_mod.launch_mpv({"media_path": media.name}, claimed)
        self.assertIsNone(win_id)
        self.assertEqual(claimed, set())


if __name__ == "__main__":
    unittest.main()
