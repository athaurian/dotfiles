"""Tests for nvim RPC response extraction."""

import unittest

from session_manager_lib.nvim.rpc import extract_json


class TestExtractJson(unittest.TestCase):
    def test_finds_dict_with_marker(self):
        text = 'some preamble\n{"pid": 42, "buffers": []}'
        result = extract_json(text, "pid")
        self.assertEqual(result, {"pid": 42, "buffers": []})

    def test_marker_in_second_object(self):
        text = '{"other": 1} {"pid": 7}'
        self.assertEqual(extract_json(text, "pid"), {"pid": 7})

    def test_text_is_vim_warning(self):
        text = "E185: Cannot find color scheme 'nope'\n{...}"
        self.assertIsNone(extract_json(text, "pid"))

    def test_no_marker_returns_none(self):
        self.assertIsNone(extract_json('{"a": 1}', "pid"))

    def test_garbage_returns_none(self):
        self.assertIsNone(extract_json("not json at all", "pid"))

    def test_braces_inside_string_are_skipped(self):
        text = '"hello {" world\n{"pid": 3}'
        self.assertEqual(extract_json(text, "pid"), {"pid": 3})


if __name__ == "__main__":
    unittest.main()
