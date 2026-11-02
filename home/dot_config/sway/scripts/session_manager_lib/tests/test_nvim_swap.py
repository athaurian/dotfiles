"""Tests for Neovim snapshot path parsing and swapfile cleanup."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.nvim.swap as swap_mod
from session_manager_lib.config import escape_cwd


class TestParseVimToken(unittest.TestCase):
    def test_stops_at_whitespace(self):
        self.assertEqual(swap_mod._parse_vim_token("one two"), "one")

    def test_honours_backslash_escapes(self):
        self.assertEqual(
            swap_mod._parse_vim_token(r"/tmp/my\ file.txt rest"),
            "/tmp/my file.txt",
        )


class TestExtractPathFromLine(unittest.TestCase):
    def test_reads_edit_lines(self):
        self.assertEqual(
            swap_mod._extract_path_from_line("edit /tmp/notes.txt"),
            "/tmp/notes.txt",
        )

    def test_drops_the_line_number_from_badd(self):
        self.assertEqual(
            swap_mod._extract_path_from_line("badd +12 /tmp/notes.txt"),
            "/tmp/notes.txt",
        )

    def test_reads_cd_lines(self):
        self.assertEqual(
            swap_mod._extract_path_from_line("cd /tmp/project"),
            "/tmp/project",
        )

    def test_ignores_unrelated_lines(self):
        self.assertIsNone(swap_mod._extract_path_from_line("set number"))


class SwapTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.snapshot = self.root / "session.vim"
        self.swap_dir = self.root / "nvim" / "swap"
        self.swap_dir.mkdir(parents=True)
        patcher = unittest.mock.patch.object(swap_mod, "STATE_DIR", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_snapshot(self, *lines):
        self.snapshot.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def swap_path(self, original):
        return self.swap_dir / (escape_cwd(str(Path(original).resolve())) + ".swp")


class TestCleanupStaleSwapfiles(SwapTestCase):
    def test_missing_snapshot_removes_nothing(self):
        self.assertEqual(swap_mod.cleanup_stale_swapfiles(self.snapshot), 0)

    def test_removes_a_swapfile_for_a_missing_file(self):
        missing = self.root / "gone.txt"
        self.write_snapshot(f"edit {missing}")
        swap = self.swap_path(missing)
        swap.write_text("swap", encoding="utf-8")
        self.assertEqual(swap_mod.cleanup_stale_swapfiles(self.snapshot), 1)
        self.assertFalse(swap.exists())

    def test_keeps_a_swapfile_for_an_existing_file(self):
        present = self.root / "present.txt"
        present.write_text("", encoding="utf-8")
        self.write_snapshot(f"edit {present}")
        swap = self.swap_path(present)
        swap.write_text("swap", encoding="utf-8")
        self.assertEqual(swap_mod.cleanup_stale_swapfiles(self.snapshot), 0)
        self.assertTrue(swap.exists())

    def test_keeps_a_swapfile_that_was_not_referenced(self):
        self.write_snapshot("set number")
        orphan = self.swap_dir / "orphan.swp"
        orphan.write_text("swap", encoding="utf-8")
        self.assertEqual(swap_mod.cleanup_stale_swapfiles(self.snapshot), 0)
        self.assertTrue(orphan.exists())

    def test_unlink_failure_is_reported_as_zero(self):
        missing = self.root / "gone.txt"
        self.write_snapshot(f"edit {missing}")
        self.swap_path(missing).write_text("swap", encoding="utf-8")
        with unittest.mock.patch.object(Path, "unlink", side_effect=OSError("busy")):
            self.assertEqual(swap_mod.cleanup_stale_swapfiles(self.snapshot), 0)


if __name__ == "__main__":
    unittest.main()
