"""Tests for zathura state capture and restore."""

import tempfile
import unittest
import unittest.mock

import session_manager_lib.apps.generic as gen_mod
import session_manager_lib.apps.zathura as zathura_mod
from session_manager_lib.tests.helpers import FakeWatcher, RecordingPopen


def bus_reply(stdout="", returncode=0):
    return unittest.mock.Mock(returncode=returncode, stdout=stdout)


class TestGetZathuraInfo(unittest.TestCase):
    def test_reads_document_and_page_over_dbus(self):
        replies = [
            bus_reply('s "/tmp/book.pdf"\n'),
            bus_reply("uint32 12\n"),
        ]
        with unittest.mock.patch.object(
            zathura_mod.subprocess, "run", side_effect=replies
        ) as run:
            self.assertEqual(zathura_mod.get_zathura_info(10), ("/tmp/book.pdf", 12))
        self.assertEqual(run.call_count, 2)

    def test_falls_back_to_the_command_line_when_dbus_fails(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".pdf") as document,
            unittest.mock.patch.object(
                zathura_mod.subprocess, "run", return_value=bus_reply(returncode=1)
            ),
            unittest.mock.patch.object(
                zathura_mod,
                "read_cmdline",
                return_value=["zathura", "--flag", document.name],
            ),
        ):
            self.assertEqual(zathura_mod.get_zathura_info(10), (document.name, 0))

    def test_falls_back_when_busctl_is_missing(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".pdf") as document,
            unittest.mock.patch.object(
                zathura_mod.subprocess, "run", side_effect=OSError("missing")
            ),
            unittest.mock.patch.object(
                zathura_mod, "read_cmdline", return_value=["zathura", document.name]
            ),
        ):
            self.assertEqual(zathura_mod.get_zathura_info(10), (document.name, 0))

    def test_page_number_is_zero_when_the_property_is_unreadable(self):
        replies = [bus_reply('s "/tmp/book.pdf"\n'), bus_reply("not a number\n")]
        with unittest.mock.patch.object(
            zathura_mod.subprocess, "run", side_effect=replies
        ):
            self.assertEqual(zathura_mod.get_zathura_info(10), ("/tmp/book.pdf", 0))

    def test_returns_empty_when_nothing_is_found(self):
        with (
            unittest.mock.patch.object(
                zathura_mod.subprocess, "run", return_value=bus_reply(returncode=1)
            ),
            unittest.mock.patch.object(
                zathura_mod, "read_cmdline", return_value=["zathura", "--flag"]
            ),
        ):
            self.assertEqual(zathura_mod.get_zathura_info(10), ("", 0))


class TestLaunchZathura(unittest.TestCase):
    def _launch(self, node, win_id=66, run=None):
        popen = RecordingPopen()
        claimed = set()
        run_mock = run or unittest.mock.Mock(returncode=0)
        with (
            unittest.mock.patch.object(zathura_mod.subprocess, "Popen", popen),
            unittest.mock.patch.object(zathura_mod.subprocess, "run", run_mock),
            unittest.mock.patch.object(zathura_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(
                gen_mod, "wait_for_window_by_pid", return_value=win_id
            ),
        ):
            result = zathura_mod.launch_zathura(node, claimed)
        return result, claimed, popen, run_mock

    def test_launches_with_the_saved_document(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as document:
            result, claimed, popen, run = self._launch({"document_path": document.name})
        self.assertEqual(result, 66)
        self.assertEqual(claimed, {66})
        self.assertEqual(popen.commands, [["zathura", document.name]])
        run.assert_not_called()

    def test_launches_without_a_missing_document(self):
        result, _, popen, _ = self._launch({"document_path": "/no/such/file"})
        self.assertEqual(result, 66)
        self.assertEqual(popen.commands, [["zathura"]])

    def test_requests_the_saved_page(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as document:
            result, _, _, run = self._launch(
                {"document_path": document.name, "page_number": 7}
            )
        self.assertEqual(result, 66)
        command = run.call_args.args[0]
        self.assertIn("GotoPage", command)
        self.assertEqual(command[-1], "7")

    def test_retries_the_page_until_the_bus_accepts(self):
        run = unittest.mock.Mock(
            side_effect=[bus_reply(returncode=1), bus_reply(returncode=0)]
        )
        with (
            tempfile.NamedTemporaryFile(suffix=".pdf") as document,
            unittest.mock.patch.object(zathura_mod.time, "sleep"),
        ):
            self._launch({"document_path": document.name, "page_number": 7}, run=run)
        self.assertEqual(run.call_count, 2)

    def test_does_not_request_a_page_without_a_document(self):
        _, _, _, run = self._launch(
            {"document_path": "/no/such/file", "page_number": 7}
        )
        run.assert_not_called()

    def test_returns_none_when_no_window_appears(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as document:
            result, claimed, _, run = self._launch(
                {"document_path": document.name, "page_number": 7}, win_id=None
            )
        self.assertIsNone(result)
        self.assertEqual(claimed, set())
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
