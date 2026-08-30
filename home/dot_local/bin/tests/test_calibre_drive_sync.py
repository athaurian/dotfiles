#!/usr/bin/env python3
"""Tests for the naming logic of calibre-drive-sync.

Run from the repository root::

    make check-calibre
"""

from __future__ import annotations

import importlib.util
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "executable_calibre-drive-sync"

# The script has no .py suffix, so the loader must be given explicitly.
_LOADER = SourceFileLoader("calibre_drive_sync", str(_SCRIPT))
_SPEC = importlib.util.spec_from_loader(_LOADER.name, _LOADER)
assert _SPEC
sync = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(sync)


class FormatIndexTest(unittest.TestCase):
    def test_whole_numbers_are_zero_padded(self):
        self.assertEqual(sync.format_index(1.0), "01")
        self.assertEqual(sync.format_index(12.0), "12")

    def test_fractions_keep_their_decimal(self):
        self.assertEqual(sync.format_index(8.5), "08.5")
        self.assertEqual(sync.format_index(0.5), "00.5")


class CleanTitleTest(unittest.TestCase):
    def test_strips_series_echo_with_book_number(self):
        self.assertEqual(
            sync.clean_title(
                "The Beginning After the End, Book 01: Early Years",
                "The Beginning After the End",
            ),
            "Early Years",
        )

    def test_handles_fractional_book_numbers(self):
        self.assertEqual(
            sync.clean_title("Series, Book 08.5: Fallen", "Series"), "Fallen"
        )

    def test_leaves_unrelated_titles_alone(self):
        self.assertEqual(
            sync.clean_title("A Book of Two Ways", "Other"),
            "A Book of Two Ways",
        )

    def test_requires_the_series_prefix_to_match(self):
        self.assertEqual(
            sync.clean_title("Sequel, Book 02: More", "Series"),
            "Sequel, Book 02: More",
        )

    def test_falls_back_when_nothing_remains(self):
        self.assertEqual(
            sync.clean_title("Series, Book 1:", "Series"), "Series, Book 1:"
        )


class DisplayNameTest(unittest.TestCase):
    def test_series_books_get_author_series_and_title(self):
        entry = {
            "authors": "TurtleMe",
            "series": "The Beginning After the End",
            "series_index": 1.0,
            "title": "The Beginning After the End, Book 01: Early Years",
        }
        self.assertEqual(
            sync.display_name(entry),
            "TurtleMe - The Beginning After the End 01 - Early Years",
        )

    def test_books_without_series_drop_the_middle(self):
        entry = {"authors": "K. N. King", "series_index": 1.0, "title": "C Programming"}
        self.assertEqual(sync.display_name(entry), "K. N. King - C Programming")

    def test_missing_fields_get_placeholders(self):
        self.assertEqual(sync.display_name({}), "Unknown - Untitled")

    def test_path_separators_are_sanitized(self):
        entry = {"authors": "A/B", "title": "Down/Up"}
        self.assertEqual(sync.display_name(entry), "A_B - Down_Up")


class PlanNamesTest(unittest.TestCase):
    def test_unique_names_pass_through(self):
        books = [Path("/l/A/a.epub"), Path("/l/B/b.pdf")]
        self.assertEqual(sync.plan_names(books, None), ["a.epub", "b.pdf"])

    def test_collisions_get_a_stable_hash_suffix(self):
        books = [Path("/l/One/x.epub"), Path("/l/Two/x.epub")]
        planned = sync.plan_names(books, None)
        self.assertRegex(planned[0], r"^x \[[0-9a-f]{8}\]\.epub$")
        self.assertNotEqual(planned[0], planned[1])
        self.assertEqual(planned, sync.plan_names(books, None))

    def test_metadata_names_are_used_when_available(self):
        books = [Path("/l/TurtleMe/Some Book (1)/t.epub")]
        metadata = {
            str(books[0]): {
                "authors": "TurtleMe",
                "series": "Saga",
                "series_index": 3.0,
                "title": "Some Book",
            }
        }
        self.assertEqual(
            sync.plan_names(books, metadata), ["TurtleMe - Saga 03 - Some Book.epub"]
        )


if __name__ == "__main__":
    unittest.main()
