"""Tests for ``picker_lib.dunst_hist`` covering menu building and id lookup."""

import json
import unittest
import unittest.mock

from picker_lib import dunst_hist

# Shape of real ``dunstctl history`` output. Prints {"data": [[entry, ...]]} with
# every field wrapped as {"type": ..., "data": value}.
TYPED = {
    "data": [
        [
            {
                "id": {"type": "i", "data": 7},
                "summary": {"type": "s", "data": "Update: kernel 6.9: reboot?"},
                "body": {"type": "s", "data": "see http://h:1/x: now"},
                "appname": {"type": "s", "data": "testapp"},
                "urgency": {"type": "s", "data": "NORMAL"},
            },
            {
                "id": {"type": "i", "data": 9},
                "summary": {"type": "s", "data": "hi — there"},
                "body": {"type": "s", "data": "a\nb\nc"},
                "appname": {"type": "s", "data": "other"},
                "urgency": {"type": "s", "data": "CRITICAL"},
            },
        ]
    ]
}

PLAIN = [
    {"id": 7, "summary": "Update: kernel 6.9: reboot?", "body": "see it"},
    {"id": 9, "summary": "hi", "body": "a\nb\nc"},
    {"id": 11},
]


class TestMenuLines(unittest.TestCase):
    def test_tab_separated_zero_padded_ids(self):
        lines = dunst_hist.menu_lines(dunst_hist._items_of(json.dumps(TYPED)))
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("0007\t"))
        self.assertIn("reboot?", lines[0])

    def test_newlines_collapsed(self):
        lines = dunst_hist.menu_lines(dunst_hist._items_of(json.dumps(TYPED)))
        for line in lines:
            self.assertNotIn("\n", line)
        self.assertIn("a b c", lines[1])

    def test_missing_fields_tolerated(self):
        lines = dunst_hist.menu_lines(PLAIN)
        self.assertTrue(lines[2].startswith("0011\t"))

    def test_non_numeric_id_skipped(self):
        lines = dunst_hist.menu_lines([{"id": "nan!", "summary": "x"}])
        self.assertEqual(lines, [])


class TestLookup(unittest.TestCase):
    def test_exact_summary_and_body_with_colons(self):
        raw = json.dumps(TYPED)
        summary, body = dunst_hist.lookup(raw, 7)
        self.assertEqual(summary, "Update: kernel 6.9: reboot?")
        self.assertEqual(body, "see http://h:1/x: now")

    def test_unknown_id_returns_blanks(self):
        self.assertEqual(dunst_hist.lookup(json.dumps(TYPED), 999), ("", ""))

    def test_plain_shape(self):
        raw = json.dumps({"data": PLAIN})
        self.assertEqual(dunst_hist.lookup(raw, 9), ("hi", "a\nb\nc"))

    def test_invalid_json_returns_blanks(self):
        self.assertEqual(dunst_hist.lookup("not json", 7), ("", ""))


class TestItemsOf(unittest.TestCase):
    def test_flattens_grouped_lists(self):
        items = dunst_hist._items_of(json.dumps(TYPED))
        self.assertEqual([item["id"] for item in items], [7, 9])

    def test_dedupes_repeated_ids(self):
        raw = json.dumps({"data": [PLAIN, PLAIN]})
        items = dunst_hist._items_of(raw)
        self.assertEqual([item["id"] for item in items], [7, 9, 11])

    def test_empty_history(self):
        self.assertEqual(dunst_hist._items_of('{"data": [[]]}'), [])


class TestFetch(unittest.TestCase):
    def test_history_parsed(self):
        payload = json.dumps(TYPED)

        with unittest.mock.patch.object(
            dunst_hist, "_run_dunstctl", return_value=payload
        ):
            items, raw = dunst_hist.fetch()
        self.assertEqual([item["id"] for item in items], [7, 9])
        self.assertEqual(raw, payload)

    def test_empty_returns_none(self):
        with unittest.mock.patch.object(
            dunst_hist, "_run_dunstctl", return_value='{"data": [[]]}'
        ):
            self.assertEqual(dunst_hist.fetch(), (None, ""))

    def test_unavailable_returns_none(self):
        with unittest.mock.patch.object(dunst_hist, "_run_dunstctl", return_value=None):
            self.assertEqual(dunst_hist.fetch(), (None, ""))

    def test_restore_latest_pops_history(self):
        calls = []

        def fake_run(args):
            calls.append(args)
            return ""

        with unittest.mock.patch.object(dunst_hist, "_run_dunstctl", fake_run):
            dunst_hist.restore_latest()
        self.assertEqual(calls, [["history-pop"]])


if __name__ == "__main__":
    unittest.main()
