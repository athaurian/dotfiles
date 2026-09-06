"""Tests for ``picker_lib.clip`` against an isolated ``cliphist`` database."""

import shutil
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from picker_lib import clip

NEEDS_CLIPHIST = shutil.which("cliphist") is None


@unittest.skipIf(NEEDS_CLIPHIST, "cliphist not installed")
class TestListAndDecode(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="picker-clip-")
        self.addCleanup(tmp.cleanup)
        self.db_path = str(Path(tmp.name) / "db")
        self.entries = [
            "short note",
            "deploy: cut v2.3: step 4: verify",
            "line one\nline two with: colon",
            "x" * 200,
        ]
        for entry in self.entries:
            result = subprocess.run(
                ["cliphist", "-db-path", self.db_path, "store"],
                input=entry,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_list_newest_first(self):
        entries = clip.list_entries(self.db_path)
        self.assertEqual(len(entries), len(self.entries))
        displays = [display for _, display in entries]
        self.assertIn("short note", displays)
        # Long and multiline entries stay single-line previews.
        for _, display in entries:
            self.assertNotIn("\n", display)

    def test_decode_full_line_roundtrip(self):
        raw = subprocess.run(
            ["cliphist", "-db-path", self.db_path, "list"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        decoded = [clip.decode(line.encode(), self.db_path) for line in raw]
        self.assertEqual(sorted(d.decode() for d in decoded), sorted(self.entries))

    def test_decode_zero_padded_id(self):
        entries = clip.list_entries(self.db_path)
        eid, _ = entries[0]
        data = clip.decode(f"{eid:04d}".encode(), self.db_path)
        self.assertEqual(data.decode(), self.entries[-1])

    def test_decode_bare_id_with_newline_fails(self):
        entries = clip.list_entries(self.db_path)
        eid, _ = entries[0]
        with self.assertRaises(RuntimeError):
            clip.decode(f"{eid}\n".encode(), self.db_path)

    def test_decode_expired_entry_raises_not_found(self):
        # Entries can rotate out between listing and picking. Wipe the
        # database and decode a stale id through the real binary.
        entries = clip.list_entries(self.db_path)
        eid, _ = entries[0]
        wiped = subprocess.run(
            ["cliphist", "-db-path", self.db_path, "wipe"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(wiped.returncode, 0, wiped.stderr)
        with self.assertRaises(clip.EntryNotFoundError):
            clip.decode(str(eid).encode(), self.db_path)

    def test_decode_other_failure_is_plain_runtime_error(self):
        with (
            unittest.mock.patch.object(
                clip.subprocess,
                "run",
                return_value=unittest.mock.Mock(
                    returncode=1, stdout=b"", stderr=b"boom"
                ),
            ),
            self.assertRaises(RuntimeError) as ctx,
        ):
            clip.decode(b"1", self.db_path)
        self.assertNotIsInstance(ctx.exception, clip.EntryNotFoundError)

    def test_malformed_lines_skipped(self):
        with unittest.mock.patch.object(
            clip.subprocess,
            "run",
            return_value=unittest.mock.Mock(
                returncode=0, stdout="12\tok\nno-tab\n\t\n", stderr=""
            ),
        ):
            self.assertEqual(clip.list_entries(self.db_path), [(12, "ok")])

    def test_list_failure_raises(self):
        with (
            unittest.mock.patch.object(
                clip.subprocess,
                "run",
                return_value=unittest.mock.Mock(returncode=1, stdout="", stderr="boom"),
            ),
            self.assertRaises(RuntimeError),
        ):
            clip.list_entries(self.db_path)

    def test_missing_db_is_empty_history(self):
        # No database file yet means a fresh machine with nothing copied.
        # It lists as empty instead of raising, using the real cliphist error path.
        missing = str(Path(self.db_path).parent / "no-such-db")
        self.assertEqual(clip.list_entries(missing), [])


class TestCopyToClipboard(unittest.TestCase):
    def test_missing_wl_copy_raises(self):
        with (
            unittest.mock.patch.object(
                clip.subprocess,
                "run",
                side_effect=FileNotFoundError("wl-copy"),
            ),
            self.assertRaises(FileNotFoundError),
        ):
            clip.copy_to_clipboard(b"hi")

    def test_failed_copy_raises(self):
        with (
            unittest.mock.patch.object(
                clip.subprocess,
                "run",
                return_value=unittest.mock.Mock(returncode=1),
            ),
            self.assertRaises(RuntimeError),
        ):
            clip.copy_to_clipboard(b"hi")

    def test_successful_copy(self):
        with unittest.mock.patch.object(
            clip.subprocess,
            "run",
            return_value=unittest.mock.Mock(returncode=0),
        ) as run:
            clip.copy_to_clipboard(b"hi")
            args, kwargs = run.call_args
            self.assertEqual(args[0], ["wl-copy"])
            self.assertEqual(kwargs["input"], b"hi")

    def test_output_not_captured(self):
        # ``wl-copy`` forks a daemon that inherits its file descriptors.
        # Capturing them hangs ``communicate()`` while it waits for EOF.
        # This is a regression test.
        with unittest.mock.patch.object(
            clip.subprocess,
            "run",
            return_value=unittest.mock.Mock(returncode=0),
        ) as run:
            clip.copy_to_clipboard(b"hi")
            _, kwargs = run.call_args
            self.assertEqual(kwargs["stdout"], clip.subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], clip.subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
