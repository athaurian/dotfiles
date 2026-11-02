"""Tests for the CLI entry point.

The CLI is the boundary the user sees, so an unreachable compositor has to
come out as a plain message and a non-zero exit code, not a traceback.
"""

import io
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr
from pathlib import Path

import session_manager_lib.restore as restore_mod
from session_manager_lib.__main__ import main
from session_manager_lib.ipc import IpcError
from session_manager_lib.restore import restore_session


class TestUnreachableCompositor(unittest.TestCase):
    def _run(self, action):
        stderr = io.StringIO()
        with (
            unittest.mock.patch("sys.argv", ["session_manager", action]),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            main()
        return raised.exception.code, stderr.getvalue()

    def test_save_reports_the_failure(self):
        with unittest.mock.patch(
            "session_manager_lib.save.save_session",
            side_effect=IpcError("cannot connect to /run/i3.sock: no such file"),
        ):
            code, stderr = self._run("save")
        self.assertEqual(code, 1)
        self.assertIn("Cannot reach the window manager", stderr)

    def test_restore_reports_the_failure(self):
        with unittest.mock.patch(
            "session_manager_lib.restore.restore_session",
            side_effect=IpcError("cannot connect to /run/i3.sock: no such file"),
        ):
            code, stderr = self._run("restore")
        self.assertEqual(code, 1)
        self.assertIn("Cannot reach the window manager", stderr)

    def test_diff_reports_the_failure(self):
        with unittest.mock.patch(
            "session_manager_lib.restore.diff_sessions",
            side_effect=IpcError("cannot connect to /run/i3.sock: no such file"),
        ):
            code, stderr = self._run("diff")
        self.assertEqual(code, 1)
        self.assertIn("Cannot reach the window manager", stderr)

    def test_other_errors_still_propagate(self):
        """Only the unreachable-compositor case is swallowed."""
        with (
            unittest.mock.patch(
                "session_manager_lib.save.save_session",
                side_effect=ValueError("something else went wrong"),
            ),
            self.assertRaises(ValueError),
        ):
            self._run("save")


class TestRestoreFailsFast(unittest.TestCase):
    """A dead compositor must be detected before any window is touched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        state_file = Path(self.tmp.name) / "session.json"
        state_file.write_text('{"workspaces": []}', encoding="utf-8")
        patch = unittest.mock.patch.object(restore_mod, "STATE_FILE", state_file)
        patch.start()
        self.addCleanup(patch.stop)

    def test_no_window_is_restored_when_the_compositor_is_unreachable(self):
        with (
            unittest.mock.patch(
                "session_manager_lib.restore.get_tree",
                side_effect=IpcError("cannot connect to /run/i3.sock: no such file"),
            ),
            unittest.mock.patch(
                "session_manager_lib.restore._restore_session_locked"
            ) as locked,
            self.assertRaises(IpcError),
        ):
            restore_session(notify_user=False)
        locked.assert_not_called()

    def test_the_user_is_told_the_compositor_is_unreachable(self):
        with (
            unittest.mock.patch(
                "session_manager_lib.restore.get_tree",
                side_effect=IpcError("cannot connect to /run/i3.sock: no such file"),
            ),
            unittest.mock.patch("session_manager_lib.restore.notify") as notify,
            self.assertRaises(IpcError),
        ):
            restore_session(notify_user=True)
        notify.assert_called_once()
        self.assertIn("cannot reach the window manager", notify.call_args.args[0])


class TestArgumentWiring(unittest.TestCase):
    def test_has_session_exits_zero_when_content_exists(self):
        with (
            unittest.mock.patch("sys.argv", ["session_manager", "has-session"]),
            unittest.mock.patch(
                "session_manager_lib.restore.has_restorable_content", return_value=True
            ),
            self.assertRaises(SystemExit) as raised,
        ):
            main()
        self.assertEqual(raised.exception.code, 0)

    def test_has_session_exits_one_when_empty(self):
        with (
            unittest.mock.patch("sys.argv", ["session_manager", "has-session"]),
            unittest.mock.patch(
                "session_manager_lib.restore.has_restorable_content", return_value=False
            ),
            self.assertRaises(SystemExit) as raised,
        ):
            main()
        self.assertEqual(raised.exception.code, 1)

    def test_restore_passes_the_workspace_filter(self):
        with (
            unittest.mock.patch(
                "sys.argv",
                ["session_manager", "restore", "--quiet", "--workspace", "3"],
            ),
            unittest.mock.patch(
                "session_manager_lib.restore.restore_session"
            ) as restore,
        ):
            main()
        restore.assert_called_once_with(notify_user=False, workspace_filter="3")

    def test_save_quiet_disables_notifications(self):
        with (
            unittest.mock.patch("sys.argv", ["session_manager", "save", "--quiet"]),
            unittest.mock.patch("session_manager_lib.save.save_session") as save,
        ):
            main()
        save.assert_called_once_with(notify_user=False)


if __name__ == "__main__":
    unittest.main()
