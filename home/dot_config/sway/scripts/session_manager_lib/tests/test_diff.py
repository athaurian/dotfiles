"""Tests for the live-versus-saved session diff."""

import io
import json
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

import session_manager_lib.restore as restore_mod
from session_manager_lib.tests.helpers import make_window, make_workspace


def live_tree(*workspaces):
    return {"nodes": [{"type": "output", "nodes": list(workspaces)}]}


def saved_payload(workspaces, hidden=None, background=None):
    return {
        "workspaces": list(workspaces),
        "hidden_scratchpad": list(hidden or []),
        "background_apps": list(background or []),
    }


class DiffTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_file = Path(self.tmp.name) / "session.json"
        patch = unittest.mock.patch.object(restore_mod, "STATE_FILE", self.state_file)
        patch.start()
        self.addCleanup(patch.stop)
        close = unittest.mock.patch.object(restore_mod, "close_connection")
        self.close_connection = close.start()
        self.addCleanup(close.stop)

    def run_diff(self, tree=None, payload=None):
        if payload is not None:
            self.state_file.write_text(json.dumps(payload), encoding="utf-8")
        get_tree = unittest.mock.patch.object(
            restore_mod, "get_tree", return_value=tree or live_tree()
        )
        get_tree.start()
        self.addCleanup(get_tree.stop)
        output = io.StringIO()
        with redirect_stdout(output):
            restore_mod.diff_sessions()
        return output.getvalue()


class TestUnreadableInput(DiffTestCase):
    def test_missing_state_file_is_reported(self):
        output = io.StringIO()
        with (
            unittest.mock.patch.object(restore_mod, "get_tree") as get_tree,
            redirect_stdout(output),
        ):
            restore_mod.diff_sessions()
        self.assertIn("Saved session unreadable", output.getvalue())
        get_tree.assert_not_called()

    def test_invalid_json_is_reported(self):
        self.state_file.write_text("{not json", encoding="utf-8")
        output = io.StringIO()
        with (
            unittest.mock.patch.object(restore_mod, "get_tree") as get_tree,
            redirect_stdout(output),
        ):
            restore_mod.diff_sessions()
        self.assertIn("Saved session unreadable", output.getvalue())
        get_tree.assert_not_called()

    def test_live_tree_failure_is_reported(self):
        self.state_file.write_text(json.dumps(saved_payload([])), encoding="utf-8")
        with unittest.mock.patch.object(
            restore_mod, "get_tree", side_effect=OSError("socket gone")
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                restore_mod.diff_sessions()
        self.assertIn("Cannot read live tree: socket gone", output.getvalue())
        self.close_connection.assert_called_once()


class TestWorkspaceComparison(DiffTestCase):
    def test_matching_counts_are_reported(self):
        saved = saved_payload(
            [make_workspace("1", nodes=[make_window(), make_window()])]
        )
        tree = live_tree(make_workspace("1", nodes=[make_window(), make_window()]))
        self.assertIn("ws 1: 2 windows matches saved", self.run_diff(tree, saved))

    def test_live_only_workspace_is_reported(self):
        saved = saved_payload([make_workspace("1")])
        tree = live_tree(
            make_workspace("1"), make_workspace("2", nodes=[make_window()])
        )
        output = self.run_diff(tree, saved)
        self.assertIn("ws 2: 1 live windows would remain (not in saved)", output)

    def test_saved_only_workspace_is_reported(self):
        saved = saved_payload(
            [make_workspace("1", nodes=[make_window(), make_window()])]
        )
        output = self.run_diff(live_tree(), saved)
        self.assertIn("ws 1: would create 2 windows (currently missing)", output)

    def test_count_mismatch_shows_both_sides(self):
        saved = saved_payload(
            [make_workspace("1", nodes=[make_window(), make_window()])]
        )
        output = self.run_diff(
            live_tree(make_workspace("1", nodes=[make_window()])), saved
        )
        self.assertIn("ws 1: live 1 vs saved 2 would recreate", output)

    def test_scratchpad_is_not_compared_as_a_workspace(self):
        saved = saved_payload([make_workspace("1")])
        tree = live_tree(
            make_workspace("1"),
            make_workspace("__i3_scratch", nodes=[make_window()]),
        )
        output = self.run_diff(tree, saved)
        self.assertNotIn("__i3_scratch", output)

    def test_saved_extras_are_summarised(self):
        saved = saved_payload(
            [make_workspace("1")],
            hidden=[make_window()],
            background=[{"app_id": "vesktop"}],
        )
        output = self.run_diff(live_tree(make_workspace("1")), saved)
        self.assertIn("hidden scratchpad: 1 windows saved", output)
        self.assertIn("background apps: 1 saved", output)

    def test_empty_saved_session_is_reported(self):
        output = self.run_diff(live_tree(), saved_payload([]))
        self.assertIn("Saved session is empty", output)


if __name__ == "__main__":
    unittest.main()
