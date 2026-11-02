"""Tests for Calibre ebook viewer capture and restore."""

import json
import sqlite3
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.apps.calibre as calibre_mod
import session_manager_lib.apps.generic as gen_mod
from session_manager_lib.tests.helpers import FakeWatcher, RecordingPopen


class CalibreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def patch_config(self, path):
        patcher = unittest.mock.patch.object(calibre_mod, "CALIBRE_CONFIG", path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_history(self, entries):
        path = self.root / "viewer.json"
        path.write_text(
            json.dumps({"session_data": {"standalone_recently_opened": entries}}),
            encoding="utf-8",
        )
        self.patch_config(path)
        return path

    def make_library(self, rows):
        db = self.root / "metadata.db"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, path TEXT)"
        )
        conn.execute("CREATE TABLE data (book INTEGER, format TEXT, name TEXT)")
        for book_id, title, book_path, fmt, name in rows:
            conn.execute(
                "INSERT INTO books VALUES (?, ?, ?)", (book_id, title, book_path)
            )
            if fmt:
                conn.execute("INSERT INTO data VALUES (?, ?, ?)", (book_id, fmt, name))
        conn.commit()
        conn.close()

        patcher = unittest.mock.patch.object(calibre_mod, "CALIBRE_DB", db)
        patcher.start()
        self.addCleanup(patcher.stop)
        home_patch = unittest.mock.patch.object(Path, "home", return_value=self.home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        return db

    def add_book_file(self, book_path, name):
        folder = self.home / "Library" / book_path
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text("", encoding="utf-8")
        return path


class TestCalibreTitle(unittest.TestCase):
    def test_parses_document_and_format(self):
        self.assertEqual(
            calibre_mod.calibre_title_from_window("Dune [EPUB] — E-book viewer"),
            ("Dune", "EPUB"),
        )

    def test_uppercases_the_format(self):
        self.assertEqual(
            calibre_mod.calibre_title_from_window("Dune [pdf] — E-book viewer"),
            ("Dune", "PDF"),
        )

    def test_empty_viewer_has_no_document(self):
        self.assertEqual(
            calibre_mod.calibre_title_from_window("E-book viewer"), ("", "EMPTY")
        )

    def test_other_titles_are_ignored(self):
        self.assertIsNone(calibre_mod.calibre_title_from_window("Dune — E-book viewer"))


class TestResolutionFromHistory(CalibreTestCase):
    def test_resolves_a_matching_recent_entry(self):
        media = self.root / "Dune.epub"
        media.write_text("", encoding="utf-8")
        self.write_history([{"pathtoebook": str(media), "title": "Dune"}])
        self.assertEqual(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB"),
            str(media.resolve()),
        )

    def test_treats_epub_and_kepub_as_the_same_format(self):
        media = self.root / "Dune.kepub"
        media.write_text("", encoding="utf-8")
        self.write_history([{"pathtoebook": str(media), "title": "Dune"}])
        self.assertEqual(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB"),
            str(media.resolve()),
        )

    def test_rejects_a_format_mismatch(self):
        media = self.root / "Dune.epub"
        media.write_text("", encoding="utf-8")
        self.write_history([{"pathtoebook": str(media), "title": "Dune"}])
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_history("Dune", "PDF")
        )

    def test_ignores_entries_whose_file_is_gone(self):
        self.write_history(
            [{"pathtoebook": str(self.root / "gone.epub"), "title": "Dune"}]
        )
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB")
        )

    def test_rejects_ambiguous_matches(self):
        first = self.root / "Dune.epub"
        second = self.root / "Dune-copy.epub"
        first.write_text("", encoding="utf-8")
        second.write_text("", encoding="utf-8")
        self.write_history(
            [
                {"pathtoebook": str(first), "title": "Dune"},
                {"pathtoebook": str(second), "title": "Dune"},
            ]
        )
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB")
        )

    def test_missing_config_file_is_ignored(self):
        self.patch_config(self.root / "missing.json")
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB")
        )

    def test_malformed_config_file_is_ignored(self):
        path = self.root / "viewer.json"
        path.write_text("{not json", encoding="utf-8")
        self.patch_config(path)
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_history("Dune", "EPUB")
        )


class TestResolutionFromLibrary(CalibreTestCase):
    def test_finds_a_book_in_the_library(self):
        self.make_library([(1, "Dune", "Frank Herbert/Dune (1)", "EPUB", "Dune.epub")])
        book = self.add_book_file("Frank Herbert/Dune (1)", "Dune.epub")
        self.assertEqual(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB"),
            str(book.resolve()),
        )

    def test_finds_a_filename_with_underscores(self):
        self.make_library(
            [(1, "Dune", "Frank Herbert/Dune (1)", "EPUB", "Dune Messiah.epub")]
        )
        book = self.add_book_file("Frank Herbert/Dune (1)", "Dune_Messiah.epub")
        self.assertEqual(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB"),
            str(book.resolve()),
        )

    def test_treats_epub_and_kepub_as_the_same_format(self):
        self.make_library(
            [(1, "Dune", "Frank Herbert/Dune (1)", "KEPUB", "Dune.kepub")]
        )
        book = self.add_book_file("Frank Herbert/Dune (1)", "Dune.kepub")
        self.assertEqual(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB"),
            str(book.resolve()),
        )

    def test_rejects_a_format_mismatch(self):
        self.make_library([(1, "Dune", "Frank Herbert/Dune (1)", "EPUB", "Dune.epub")])
        self.add_book_file("Frank Herbert/Dune (1)", "Dune.epub")
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_library("Dune", "PDF")
        )

    def test_rejects_ambiguous_matches(self):
        self.make_library(
            [
                (1, "Dune", "Frank Herbert/Dune (1)", "EPUB", "Dune.epub"),
                (2, "Dune", "Frank Herbert/Dune (2)", "EPUB", "Dune.epub"),
            ]
        )
        self.add_book_file("Frank Herbert/Dune (1)", "Dune.epub")
        self.add_book_file("Frank Herbert/Dune (2)", "Dune.epub")
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB")
        )

    def test_missing_database_is_ignored(self):
        self.make_library([])
        (self.root / "metadata.db").unlink()
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB")
        )

    def test_corrupt_database_is_ignored(self):
        db = self.make_library([])
        db.write_text("not a database", encoding="utf-8")
        self.assertIsNone(
            calibre_mod._resolve_calibre_document_from_library("Dune", "EPUB")
        )


class TestDocumentLookup(CalibreTestCase):
    def test_empty_viewer_returns_an_empty_path(self):
        with (
            unittest.mock.patch.object(
                calibre_mod, "_resolve_calibre_document_from_history"
            ) as history,
            unittest.mock.patch.object(
                calibre_mod, "_resolve_calibre_document_from_library"
            ) as library,
        ):
            self.assertEqual(calibre_mod.get_ebook_viewer_document("", "EMPTY"), "")
        history.assert_not_called()
        library.assert_not_called()

    def test_history_result_wins(self):
        with (
            unittest.mock.patch.object(
                calibre_mod,
                "_resolve_calibre_document_from_history",
                return_value="/from/history.epub",
            ),
            unittest.mock.patch.object(
                calibre_mod, "_resolve_calibre_document_from_library"
            ) as library,
        ):
            self.assertEqual(
                calibre_mod.get_ebook_viewer_document("Dune", "EPUB"),
                "/from/history.epub",
            )
        library.assert_not_called()

    def test_falls_back_to_the_library(self):
        with (
            unittest.mock.patch.object(
                calibre_mod,
                "_resolve_calibre_document_from_history",
                return_value=None,
            ),
            unittest.mock.patch.object(
                calibre_mod,
                "_resolve_calibre_document_from_library",
                return_value="/from/library.epub",
            ),
        ):
            self.assertEqual(
                calibre_mod.get_ebook_viewer_document("Dune", "EPUB"),
                "/from/library.epub",
            )


class TestLaunchEbookViewer(unittest.TestCase):
    def _launch(self, node, win_id=88):
        popen = RecordingPopen()
        claimed = set()
        with (
            unittest.mock.patch.object(calibre_mod.subprocess, "Popen", popen),
            unittest.mock.patch.object(calibre_mod, "WindowEventWatcher", FakeWatcher),
            unittest.mock.patch.object(
                calibre_mod, "matching_window_ids", return_value=[]
            ),
            unittest.mock.patch.object(
                gen_mod, "wait_for_app_window", return_value=win_id
            ),
        ):
            result = calibre_mod.launch_ebook_viewer(node, claimed)
        return result, claimed, popen

    def test_launches_with_the_saved_document(self):
        with tempfile.NamedTemporaryFile(suffix=".epub") as document:
            result, claimed, popen = self._launch({"document_path": document.name})
        self.assertEqual(result, 88)
        self.assertEqual(claimed, {88})
        self.assertEqual(popen.commands, [["ebook-viewer", document.name]])

    def test_launches_without_a_missing_document(self):
        result, _, popen = self._launch({"document_path": "/no/such/file"})
        self.assertEqual(result, 88)
        self.assertEqual(popen.commands, [["ebook-viewer"]])

    def test_returns_none_when_no_window_appears(self):
        result, claimed, _ = self._launch({}, win_id=None)
        self.assertIsNone(result)
        self.assertEqual(claimed, set())


if __name__ == "__main__":
    unittest.main()
