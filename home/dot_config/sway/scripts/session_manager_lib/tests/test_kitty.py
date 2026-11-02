"""Tests for the kitty terminal command builder and launcher."""

import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from session_manager_lib.apps import kitty


class BuildKittyCommandTests(unittest.TestCase):
    def test_plain_terminal_uses_directory_and_title(self):
        node = {"cwd": "/work", "name": "user@host:/work"}
        self.assertEqual(
            kitty.build_kitty_command(node),
            ["kitty", "--directory", "/work", "--title", "user@host:/work", "bash"],
        )

    def test_default_title_is_derived_from_cwd(self):
        node = {"cwd": "/work"}
        with (
            unittest.mock.patch.dict(os.environ, {"USER": "tester"}),
            unittest.mock.patch.object(kitty.os, "uname") as uname,
        ):
            uname.return_value.nodename = "box.example"
            cmd = kitty.build_kitty_command(node)
        self.assertEqual(
            cmd[:5],
            ["kitty", "--directory", "/work", "--title", "tester@box:/work"],
        )
        self.assertEqual(cmd[5:], ["bash"])

    def test_drop_terminal_forces_its_title(self):
        node = {"cwd": "/work", "name": "something-else"}
        self.assertEqual(
            kitty.build_kitty_command(node, drop=True),
            [
                "kitty",
                "--name=scratchpad_term",
                "--title=drop_term",
                "--directory",
                "/work",
                "bash",
            ],
        )

    def test_drop_terminal_sets_the_wm_class_instance_the_rule_matches(self):
        # i3 matches the dropdown on [instance="scratchpad_term"], so the
        # launcher must pass it as kitty's `--name` (the WM_CLASS instance),
        # otherwise the for_window rule never fires for a restored dropdown.
        cmd = kitty.build_kitty_command({"cwd": "/work"}, drop=True)
        self.assertIn("--name=scratchpad_term", cmd)
        self.assertIn("--title=drop_term", cmd)

    def test_plain_terminal_leaves_the_instance_alone(self):
        cmd = kitty.build_kitty_command({"cwd": "/work", "name": "user@host:/work"})
        self.assertNotIn("--name=scratchpad_term", cmd)

    def test_dashboard_opens_nvim(self):
        node = {"cwd": "/work", "name": "user@host:/work", "nvim_type": "dashboard"}
        self.assertEqual(kitty.build_kitty_command(node)[-1], "nvim")

    def test_session_restore_sources_the_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "session.vim"
            snapshot.write_text("vim session", encoding="utf-8")
            node = {
                "cwd": "/work",
                "name": "user@host:/work",
                "nvim_type": "session",
                "nvim_snapshot": str(snapshot),
            }
            cmd = kitty.build_kitty_command(node)
        self.assertEqual(cmd[-2], "-ic")
        self.assertIn(f"NVIM_RESTORE_FILE={snapshot}", cmd[-1])
        self.assertIn("nvim -c", cmd[-1])


class LaunchKittyTests(unittest.TestCase):
    def test_launch_matches_the_kitty_app_id(self):
        claimed: set[int] = set()
        proc = unittest.mock.Mock(pid=123)
        watcher = unittest.mock.MagicMock()
        with (
            unittest.mock.patch.object(
                kitty, "WindowEventWatcher", return_value=watcher
            ),
            unittest.mock.patch.object(kitty.subprocess, "Popen", return_value=proc),
            unittest.mock.patch(
                "session_manager_lib.apps.generic.wait_for_window_by_pid",
                return_value=42,
            ) as wait,
        ):
            result = kitty.launch_kitty({"cwd": "/work"}, claimed, drop=True)
        self.assertEqual(result, 42)
        self.assertEqual(wait.call_args.args[2], "kitty")
        self.assertIn(42, claimed)

    def test_launch_does_not_hold_the_callers_output_open(self):
        """A kitty that inherits stdout keeps a pipe open for the caller."""
        claimed: set[int] = set()
        proc = unittest.mock.Mock(pid=123)
        watcher = unittest.mock.MagicMock()
        with (
            unittest.mock.patch.object(
                kitty, "WindowEventWatcher", return_value=watcher
            ),
            unittest.mock.patch.object(
                kitty.subprocess, "Popen", return_value=proc
            ) as popen,
            unittest.mock.patch(
                "session_manager_lib.apps.generic.wait_for_window_by_pid",
                return_value=42,
            ),
        ):
            kitty.launch_kitty({"cwd": "/work"}, claimed)
        kwargs = popen.call_args.kwargs
        self.assertIs(kwargs["stdout"], kitty.subprocess.DEVNULL)
        self.assertIs(kwargs["stderr"], kitty.subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
