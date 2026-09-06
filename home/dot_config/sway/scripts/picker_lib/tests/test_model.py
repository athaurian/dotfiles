"""Tests for ``picker_lib.model`` covering menu line format and parsing."""

import unittest

from picker_lib import model


class TestFormatEntry(unittest.TestCase):
    def test_zero_padded_to_width_four(self):
        self.assertEqual(model.format_entry(7, "hi"), "0007\thi")

    def test_wide_ids_print_in_full(self):
        self.assertEqual(model.format_entry(12345, "hi"), "12345\thi")


class TestSplitEntry(unittest.TestCase):
    def test_roundtrip(self):
        line = model.format_entry(42, "some: text — here")
        self.assertEqual(model.split_entry(line), (42, "some: text — here"))

    def test_zero_padded_id_parses(self):
        self.assertEqual(model.split_entry("0042\ttext"), (42, "text"))

    def test_missing_tab_is_malformed(self):
        eid, display = model.split_entry("no tab here")
        self.assertIsNone(eid)
        self.assertEqual(display, "no tab here")

    def test_non_numeric_id_is_malformed(self):
        eid, _ = model.split_entry("ab\ttext")
        self.assertIsNone(eid)


class TestSingleLine(unittest.TestCase):
    def test_newlines_become_spaces(self):
        self.assertEqual(model.single_line("a\nb\nc"), "a b c")

    def test_surrounding_whitespace_stripped(self):
        self.assertEqual(model.single_line("  a\n"), "a")


if __name__ == "__main__":
    unittest.main()
