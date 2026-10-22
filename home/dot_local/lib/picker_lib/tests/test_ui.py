"""Tests for ``picker_lib.ui``: fzf invocation and kitty relaunch."""

import unittest
import unittest.mock

from picker_lib import ui


class TestRunFzf(unittest.TestCase):
    def test_have(self):
        with unittest.mock.patch.object(
            ui.shutil, "which", return_value="/usr/bin/fzf"
        ):
            self.assertTrue(ui.have("fzf"))
        with unittest.mock.patch.object(ui.shutil, "which", return_value=None):
            self.assertFalse(ui.have("fzf"))

    def test_fzf_args_and_input(self):
        result = unittest.mock.Mock(returncode=0, stdout="12\tdisplay\n")
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=result
        ) as run:
            selected = ui.run_fzf(
                ["12\tdisplay"],
                prompt="prompt",
                header="header",
                preview_cmd="python preview",
            )
        self.assertEqual(selected, "12\tdisplay")
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], "fzf")
        self.assertIn("--nth=2", args[0])
        self.assertIn("--tabstop=2", args[0])
        self.assertIn("--preview=python preview", args[0])
        self.assertEqual(kwargs["input"], "12\tdisplay\n")
        self.assertTrue(kwargs["capture_output"])

    def test_cancel_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", return_value=unittest.mock.Mock(returncode=130)
        ):
            self.assertIsNone(
                ui.run_fzf(["1\tx"], prompt="p", header="h", preview_cmd="preview")
            )

    def test_empty_selection_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess,
            "run",
            return_value=unittest.mock.Mock(returncode=0, stdout="\n"),
        ):
            self.assertIsNone(
                ui.run_fzf(["1\tx"], prompt="p", header="h", preview_cmd="preview")
            )

    def test_missing_fzf_returns_none(self):
        with unittest.mock.patch.object(
            ui.subprocess, "run", side_effect=FileNotFoundError("fzf")
        ):
            self.assertIsNone(
                ui.run_fzf(["1\tx"], prompt="p", header="h", preview_cmd="preview")
            )


class TestRelaunchInKitty(unittest.TestCase):
    def test_relaunch_argv(self):
        with (
            unittest.mock.patch.object(
                ui.shutil, "which", return_value="/usr/bin/kitty"
            ),
            unittest.mock.patch.object(ui.os, "execvp") as execvp,
        ):
            self.assertTrue(ui.relaunch_in_kitty(["prog", "--ui", "fzf"]))
        execvp.assert_called_once_with(
            "/usr/bin/kitty",
            [
                "/usr/bin/kitty",
                "--title",
                "clipboard_term",
                "-e",
                "prog",
                "--ui",
                "fzf",
            ],
        )

    def test_missing_kitty_returns_false(self):
        with unittest.mock.patch.object(ui.shutil, "which", return_value=None):
            self.assertFalse(ui.relaunch_in_kitty(["prog"]))


if __name__ == "__main__":
    unittest.main()
