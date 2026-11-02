"""Tests for nvim RPC response extraction."""

import subprocess
import unittest
import unittest.mock

import session_manager_lib.nvim.rpc as rpc_mod
from session_manager_lib.nvim.rpc import extract_json, vim_single_quote


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


class TestVimSingleQuote(unittest.TestCase):
    def test_escapes_single_quotes(self):
        self.assertEqual(vim_single_quote("a'b"), "'a''b'")


class TestNvimRpc(unittest.TestCase):
    def test_returns_json_from_stdout(self):
        completed = unittest.mock.Mock(stdout='{"pid": 5}', stderr="")
        with unittest.mock.patch.object(
            rpc_mod.subprocess, "run", return_value=completed
        ) as run:
            result = rpc_mod.nvim_rpc("/tmp/nvim.sock", "return 1", "pid")
        self.assertEqual(result, {"pid": 5})
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ["nvim", "--headless", "--server"])
        self.assertIn("json_encode(luaeval('return 1'))", command[-1])
        self.assertNotIn("NVIM", run.call_args.kwargs["env"])

    def test_reads_json_from_stderr(self):
        completed = unittest.mock.Mock(stdout="", stderr='{"pid": 6}')
        with unittest.mock.patch.object(
            rpc_mod.subprocess, "run", return_value=completed
        ):
            self.assertEqual(rpc_mod.nvim_rpc("/tmp/nvim.sock", "x", "pid"), {"pid": 6})

    def test_timeout_returns_none(self):
        with unittest.mock.patch.object(
            rpc_mod.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("nvim", 1),
        ):
            self.assertIsNone(rpc_mod.nvim_rpc("/tmp/nvim.sock", "x", "pid"))


if __name__ == "__main__":
    unittest.main()
