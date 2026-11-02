"""Tests for live Neovim inspection."""

import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.nvim.inspect as inspect_mod


def socket_pid(path):
    return int(path.name.split(".")[1])


class FakeCache:
    def __init__(self, nvim_pid=None, descendants=None):
        self.nvim_pid = nvim_pid
        self._descendants = descendants or []

    def get_nvim_pid(self, pid):
        return self.nvim_pid

    def descendants(self, pid):
        return self._descendants


class TestIsDashboardState(unittest.TestCase):
    def test_empty_buffer_list_is_a_dashboard(self):
        self.assertTrue(inspect_mod.is_dashboard_state({"buffers": []}))

    def test_named_normal_buffer_is_not_a_dashboard(self):
        state = {"buffers": [{"name": "/tmp/a.txt", "buftype": ""}]}
        self.assertFalse(inspect_mod.is_dashboard_state(state))

    def test_unnamed_and_special_buffers_are_ignored(self):
        state = {
            "buffers": [
                {"name": "", "buftype": ""},
                {"name": "/tmp/term", "buftype": "terminal"},
            ]
        }
        self.assertTrue(inspect_mod.is_dashboard_state(state))


class TestInspectSocket(unittest.TestCase):
    def test_prefers_the_pid_reported_by_neovim(self):
        state = {"pid": 20, "buffers": []}
        with (
            unittest.mock.patch.object(inspect_mod, "sock_pid", return_value=10),
            unittest.mock.patch.object(inspect_mod, "nvim_rpc", return_value=state),
        ):
            self.assertEqual(
                inspect_mod.inspect_nvim_socket(Path("/run/nvim.10.0")), (20, state)
            )

    def test_keeps_the_socket_pid_when_rpc_fails(self):
        with (
            unittest.mock.patch.object(inspect_mod, "sock_pid", return_value=10),
            unittest.mock.patch.object(inspect_mod, "nvim_rpc", return_value=None),
        ):
            self.assertEqual(
                inspect_mod.inspect_nvim_socket(Path("/run/nvim.10.0")), (10, None)
            )


class TestTerminalState(unittest.TestCase):
    def _state(self, cache, sockets, inspected=None):
        inspected = inspected or (20, {"cwd": "/tmp"})
        with (
            unittest.mock.patch.object(
                inspect_mod, "runtime_nvim_sockets", return_value=sockets
            ),
            unittest.mock.patch.object(inspect_mod, "sock_pid", side_effect=socket_pid),
            unittest.mock.patch.object(
                inspect_mod, "inspect_nvim_socket", return_value=inspected
            ),
        ):
            return inspect_mod.get_terminal_nvim_state(30, cache)

    def test_returns_none_without_a_neovim_process(self):
        self.assertEqual(
            inspect_mod.get_terminal_nvim_state(30, FakeCache()), (None, None)
        )

    def test_inspects_the_direct_socket(self):
        cache = FakeCache(nvim_pid=20)
        self.assertEqual(
            self._state(cache, [Path("/run/nvim.20.0")]), (20, {"cwd": "/tmp"})
        )

    def test_inspects_a_descendant_socket(self):
        cache = FakeCache(nvim_pid=20, descendants=[31])
        self.assertEqual(
            self._state(cache, [Path("/run/nvim.31.0")], (31, {"cwd": "/tmp"})),
            (31, {"cwd": "/tmp"}),
        )

    def test_reports_the_pid_without_state_when_no_socket_matches(self):
        cache = FakeCache(nvim_pid=20)
        self.assertEqual(self._state(cache, []), (20, None))


if __name__ == "__main__":
    unittest.main()
