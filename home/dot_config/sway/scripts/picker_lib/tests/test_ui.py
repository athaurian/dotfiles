"""Tests for ``picker_lib.ui`` covering fuzzel and fzf invocation and foot relaunch."""

import subprocess
import unittest
import unittest.mock

from picker_lib import ui


def _completed(stdout="", returncode=0):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=""
    )


class TestRunFuzzel(unittest.TestCase):
    def test_returns_stripped_selection(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=_completed("0007\thi\n")
        ) as run:
            self.assertEqual(
                ui.run_fuzzel(["0007\thi"], prompt="> ", placeholder="ph"),
                "0007\thi",
            )
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "fuzzel")
        for flag in ("--dmenu", "--match-nth=2", "--tabs=2"):
            self.assertIn(flag, argv)

    def test_cancel_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=_completed("", returncode=1)
        ):
            self.assertIsNone(ui.run_fuzzel(["a"], prompt="> ", placeholder="ph"))

    def test_missing_binary_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", side_effect=FileNotFoundError("fuzzel")
        ):
            self.assertIsNone(ui.run_fuzzel(["a"], prompt="> ", placeholder="ph"))


class TestRunFzf(unittest.TestCase):
    def test_returns_stripped_selection(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=_completed("0042\thi\n")
        ) as run:
            self.assertEqual(
                ui.run_fzf(
                    ["0042\thi"],
                    prompt="> ",
                    header="h",
                    preview_cmd="true",
                ),
                "0042\thi",
            )
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "fzf")
        for flag in ("--nth=2", "--tabstop=2", "--preview=true"):
            self.assertIn(flag, argv)

    def test_escape_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=_completed("", returncode=130)
        ):
            self.assertIsNone(
                ui.run_fzf(["a"], prompt="> ", header="h", preview_cmd="true")
            )


class TestRelaunchInFoot(unittest.TestCase):
    def test_execs_foot_with_picker_app_id(self):
        with (
            unittest.mock.patch.object(
                ui.shutil, "which", return_value="/usr/bin/foot"
            ),
            unittest.mock.patch.object(ui.os, "execvp") as execvp,
        ):
            self.assertTrue(ui.relaunch_in_foot(["prog", "--ui", "fzf"]))
        execvp.assert_called_once_with(
            "/usr/bin/foot",
            ["/usr/bin/foot", "--app-id=foot_clipboard", "-e", "prog", "--ui", "fzf"],
        )

    def test_missing_foot_returns_false(self):
        with unittest.mock.patch.object(ui.shutil, "which", return_value=None):
            self.assertFalse(ui.relaunch_in_foot(["prog"]))


if __name__ == "__main__":
    unittest.main()
