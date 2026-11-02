"""Tests for the shared app launcher helpers."""

import subprocess
import unittest
import unittest.mock

from session_manager_lib.apps._common import normalize_title, reap_if_needed


class TestNormalizeTitle(unittest.TestCase):
    def test_strips_and_lowercases(self):
        self.assertEqual(normalize_title("  Hello World  "), "hello world")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize_title("Tab\t  A\nB"), "tab a b")

    def test_empty_title(self):
        self.assertEqual(normalize_title("   "), "")

    def test_titles_match_after_normalization(self):
        self.assertEqual(normalize_title("Tab  A"), normalize_title("tab a"))


class TestReapIfNeeded(unittest.TestCase):
    def test_reaps_an_exited_process(self):
        process = unittest.mock.Mock()
        process.poll.return_value = 0
        reap_if_needed(process)
        process.wait.assert_called_once_with(timeout=0)

    def test_leaves_a_running_process_alone(self):
        process = unittest.mock.Mock()
        process.poll.return_value = None
        reap_if_needed(process)
        process.wait.assert_not_called()

    def test_accepts_no_process(self):
        reap_if_needed(None)

    def test_swallows_wait_errors(self):
        for error in (OSError("gone"), subprocess.TimeoutExpired("cmd", 0)):
            process = unittest.mock.Mock()
            process.poll.return_value = 1
            process.wait.side_effect = error
            reap_if_needed(process)

    def test_swallows_poll_errors(self):
        process = unittest.mock.Mock()
        process.poll.side_effect = OSError("bad")
        reap_if_needed(process)


if __name__ == "__main__":
    unittest.main()
