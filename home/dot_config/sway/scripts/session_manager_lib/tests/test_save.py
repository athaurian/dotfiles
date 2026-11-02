"""Tests for the save orchestration: focused-workspace capture and the
end-to-end save payload assembly (hermetic)."""

import json
import tempfile
import unittest
import unittest.mock
from contextlib import nullcontext
from pathlib import Path

import session_manager_lib.save as save_mod
from session_manager_lib.ipc import IpcError
from session_manager_lib.tests.helpers import make_window, make_workspace


def make_output(nodes):
    return {"type": "output", "nodes": nodes}


class TestFocusedWorkspaceName(unittest.TestCase):
    def _tree(self, ws_nodes):
        return {"nodes": [make_output(ws_nodes)]}

    def test_finds_focused_via_leaf_ancestor(self):
        """Sway marks only the focused LEAF container. The workspace name
        must come from the ancestor walk."""
        ws3 = make_workspace("3", nodes=[make_window("kitty")])
        ws3["nodes"][0]["focused"] = True
        tree = self._tree([make_workspace("1"), ws3])
        self.assertEqual(save_mod._focused_workspace_name(tree), "3")

    def test_focused_workspace_itself(self):
        ws = make_workspace("2", nodes=[], floating=[])
        ws["focused"] = True
        self.assertEqual(save_mod._focused_workspace_name(self._tree([ws])), "2")

    def test_focused_window_in_scratchpad_ignored(self):
        scratch = make_workspace("__i3_scratch", nodes=[], floating=[])
        win = make_window("kitty")
        win["focused"] = True
        scratch["floating_nodes"] = [win]
        tree = self._tree([make_workspace("1"), scratch])
        self.assertIsNone(save_mod._focused_workspace_name(tree))

    def test_nothing_focused(self):
        tree = self._tree([make_workspace("1")])
        self.assertIsNone(save_mod._focused_workspace_name(tree))


class TestSaveSession(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.state_file = tmp / "sway_session.json"
        self.bg_file = tmp / "sway_session_background_apps.json"
        self.state_dir = tmp / "state"
        self.nvim_dir = tmp / "nvim" / "sessions"
        self.tree = {
            "nodes": [
                make_output(
                    [
                        make_workspace(
                            "1",
                            nodes=[make_window("kitty", name="kitty", pid=10)],
                            floating=[],
                        )
                    ]
                )
            ]
        }
        self.tree["nodes"][0]["nodes"][0]["focused"] = True

        self.patches = [
            unittest.mock.patch.object(save_mod, "get_tree", lambda: self.tree),
            unittest.mock.patch.object(
                save_mod, "operation_lock", lambda _dir: nullcontext()
            ),
            unittest.mock.patch.object(save_mod, "STATE_DIR", self.state_dir),
            unittest.mock.patch.object(save_mod, "STATE_FILE", self.state_file),
            unittest.mock.patch.object(save_mod, "NVIM_SESSION_DIR", self.nvim_dir),
            unittest.mock.patch.object(save_mod, "BACKGROUND_APPS_FILE", self.bg_file),
            unittest.mock.patch.object(save_mod, "notify"),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def _fake_snapshot(self):
        cache = unittest.mock.Mock()
        cache.get_terminal_cwd.return_value = "/home/user/proj"
        cache.get_nvim_pid.return_value = None
        return cache

    def _save(self):
        with (
            unittest.mock.patch.object(save_mod, "ProcCache") as pc_cls,
            unittest.mock.patch.object(
                save_mod,
                "clean_tree",
                side_effect=lambda node, _cache: dict(node),
            ),
            unittest.mock.patch.object(
                save_mod,
                "clean_floating",
                side_effect=lambda node, _cache: [dict(node)],
            ),
        ):
            pc_cls.snapshot.return_value = self._fake_snapshot()
            save_mod.save_session(notify_user=False)

    def _backup(self, suffix):
        return self.state_file.with_name(f"{self.state_file.name}.{suffix}")

    def test_saves_payload_with_focused_workspace(self):
        cleaned = {
            "type": "workspace",
            "layout": "splith",
            "nodes": [make_window("kitty", name="kitty", pid=10)],
            "floating_nodes": [],
        }
        with (
            unittest.mock.patch.object(save_mod, "ProcCache") as pc_cls,
            unittest.mock.patch.object(
                save_mod, "clean_tree", lambda node, cache: dict(cleaned)
            ),
        ):
            pc_cls.snapshot.return_value = self._fake_snapshot()
            save_mod.save_session(notify_user=False)

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 2)
        self.assertEqual(payload["focused_workspace"], "1")
        self.assertEqual(len(payload["workspaces"]), 1)
        self.assertEqual(payload["workspaces"][0]["name"], "1")
        self.assertEqual(len(payload["hidden_scratchpad"]), 0)
        self.assertIsInstance(payload["background_apps"], list)
        self.assertTrue(self.bg_file.exists())

    def test_no_focused_workspace_when_none(self):
        del self.tree["nodes"][0]["nodes"][0]["focused"]
        with unittest.mock.patch.object(save_mod, "ProcCache") as pc_cls:
            pc_cls.snapshot.return_value = self._fake_snapshot()
            save_mod.save_session(notify_user=False)
        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertIsNone(payload["focused_workspace"])

    def test_atomic_write_replaces_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out.json"
            target.write_text("old", encoding="utf-8")
            save_mod._atomic_write(target, "new")
            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            leftovers = [f for f in Path(tmp).iterdir() if f.name != "out.json"]
            self.assertEqual(leftovers, [])

    def test_hidden_scratchpad_windows_are_saved(self):
        scratch = make_workspace(
            "__i3_scratch",
            nodes=[make_window("kitty")],
            floating=[make_window("kitty")],
        )
        self.tree["nodes"][0]["nodes"].append(scratch)
        self._save()
        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["hidden_scratchpad"]), 2)

    def test_previous_saves_are_rotated(self):
        self.state_file.write_text("current", encoding="utf-8")
        for suffix, content in (("1", "one"), ("2", "two"), ("3", "three")):
            self._backup(suffix).write_text(content, encoding="utf-8")
        self._save()
        self.assertEqual(self._backup("1").read_text(encoding="utf-8"), "current")
        self.assertEqual(self._backup("2").read_text(encoding="utf-8"), "one")
        self.assertEqual(self._backup("3").read_text(encoding="utf-8"), "two")

    def test_rotation_failure_does_not_block_the_save(self):
        self.state_file.write_text("current", encoding="utf-8")
        with unittest.mock.patch.object(Path, "replace", side_effect=OSError("busy")):
            self._save()
        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 2)

    def test_helium_windows_wait_for_the_session_files(self):
        self.tree["nodes"][0]["nodes"][0]["nodes"].append(make_window("helium"))
        with unittest.mock.patch.object(save_mod.time, "sleep") as sleep:
            self._save()
        sleep.assert_called_once_with(0.8)


class TestUnreachableCompositor(unittest.TestCase):
    """A dead IPC socket must not produce a traceback."""

    def test_save_reports_the_failure_instead_of_raising(self):
        def dead_tree():
            raise IpcError("cannot connect to /run/i3.sock: no such file")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with (
                unittest.mock.patch.object(save_mod, "get_tree", dead_tree),
                unittest.mock.patch.object(
                    save_mod, "operation_lock", lambda _dir: nullcontext()
                ),
                unittest.mock.patch.object(save_mod, "STATE_DIR", tmp_path / "state"),
                unittest.mock.patch.object(
                    save_mod, "STATE_FILE", tmp_path / "state" / "sway_session.json"
                ),
                unittest.mock.patch.object(save_mod, "notify") as notify,
            ):
                # No exception escapes: the caller gets a message instead.
                save_mod.save_session(notify_user=True)
            notify.assert_called_once()
            self.assertIn("cannot reach the window manager", notify.call_args.args[0])

    def test_save_writes_no_state_file(self):
        def dead_tree():
            raise IpcError("cannot connect to /run/i3.sock: no such file")

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state" / "sway_session.json"
            with (
                unittest.mock.patch.object(save_mod, "get_tree", dead_tree),
                unittest.mock.patch.object(
                    save_mod, "operation_lock", lambda _dir: nullcontext()
                ),
                unittest.mock.patch.object(save_mod, "STATE_DIR", Path(tmp) / "state"),
                unittest.mock.patch.object(save_mod, "STATE_FILE", state_file),
                unittest.mock.patch.object(save_mod, "notify"),
            ):
                save_mod.save_session(notify_user=False)
            self.assertFalse(state_file.exists())


if __name__ == "__main__":
    unittest.main()
