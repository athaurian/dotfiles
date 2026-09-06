"""Tests for restore orchestration: payload normalisation, focused-workspace,
and floating-window restore branches."""

import unittest

from session_manager_lib.tests.helpers import (
    RestoreHarnessTestCase,
    make_con,
    make_window,
    make_workspace,
)


class TestNormalisePayload(RestoreHarnessTestCase):
    def _norm(self, payload):
        return self.restore_mod._normalise_restore_payload(payload)

    def test_legacy_list_payload(self):
        ws = make_workspace("1")
        workspaces, scratchpad, bg, focused = self._norm([ws])
        self.assertEqual(workspaces, [ws])
        self.assertEqual(scratchpad, [])
        self.assertIsNone(bg)
        self.assertIsNone(focused)

    def test_dict_payload_roundtrip(self):
        ws = make_workspace("1")
        payload = {
            "workspaces": [ws],
            "hidden_scratchpad": [],
            "background_apps": [{"app_id": "vesktop"}],
            "focused_workspace": "3",
        }
        workspaces, scratchpad, bg, focused = self._norm(payload)
        self.assertEqual(workspaces, [ws])
        self.assertEqual(scratchpad, [])
        self.assertEqual(bg, [{"app_id": "vesktop"}])
        self.assertEqual(focused, "3")

    def test_focused_workspace_absent_is_none(self):
        payload = {"workspaces": [make_workspace("1")]}
        _, _, _, focused = self._norm(payload)
        self.assertIsNone(focused)

    def test_invalid_focused_workspace_rejected(self):
        for bad in ("", 42, ["1"]):
            payload = {"workspaces": [], "focused_workspace": bad}
            with self.assertRaises(self.restore_mod.StateValidationError):
                self._norm(payload)

    def test_non_list_payload_rejected(self):
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm("not a payload")

    def test_workspace_type_enforced(self):
        payload = {"workspaces": [make_window("foot")]}
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm(payload)

    def test_missing_layout_rejected(self):
        ws = make_workspace("1")
        del ws["layout"]
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})

    def test_invalid_mark_types_rejected(self):
        win = make_window("foot", marks=[42])
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})


class TestRestoreNode(RestoreHarnessTestCase):
    def test_workspace_restores_tiled_and_floating_children(self):
        win = make_window("foot", cwd="/tmp")
        ws = make_workspace(
            "1", nodes=[win], floating=[make_window("foot", cwd="/tmp")]
        )
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("workspace 1")
        self.assertCommand("[con_id=1000] focus")
        self.assertCommand("[con_id=1001] floating enable")

    def test_con_with_only_floating_children(self):
        con = make_con(nodes=[], floating=[make_window("foot", cwd="/tmp")])
        ws = make_workspace("1", nodes=[con])
        ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("floating enable")
        self.assertCommand("resize set width 800 px")
        self.assertEqual(len(ctx.claimed_ids), 1)

    def test_empty_con_is_pruned(self):
        con = make_con(nodes=[], floating=[])
        ws = make_workspace("1", nodes=[con])
        ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertEqual(len(ctx.claimed_ids), 0)
        self.assertEqual([c for c in self.calls if "con_id=" in c], [])

    def test_con_tabbed_uses_split_h(self):
        win_a = make_window("foot", cwd="/a")
        win_b = make_window("foot", cwd="/b")
        con = make_con(nodes=[win_a, win_b], layout="tabbed")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertIn("split h", self.calls)
        self.assertIn("layout tabbed", self.calls)
        ids = [c for c in self.calls if c.startswith("[con_id=")]
        self.assertEqual(len(ids), 2)

    def test_con_splitv_uses_split_v(self):
        win_a = make_window("foot", cwd="/a")
        win_b = make_window("foot", cwd="/b")
        con = make_con(nodes=[win_a, win_b], layout="splitv")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertIn("split v", self.calls)
        self.assertIn("layout splitv", self.calls)

    def test_marks_applied_to_restored_window(self):
        win = make_window("foot", marks=["foo", "bar"])
        ws = make_workspace("1", nodes=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("mark foo")
        self.assertCommand("mark bar")


class TestRestoreFloating(RestoreHarnessTestCase):
    def _floating(self, node):
        ws = make_workspace("1", floating=[node])
        return self.restore_workspaces({"workspaces": [ws]})

    def test_foot_drop_only_geometry(self):
        self._floating(make_window("foot_drop"))
        self.assertCommand("move position 0 0")
        self.assertCommand("resize set width 800 px")
        joined = " ".join(self.calls)
        self.assertNotIn("floating enable", joined)
        self.assertNotIn("border normal", joined)
        self.assertNotIn("scratchpad", joined)

    def test_scratchpad_window_moved_to_scratchpad(self):
        self._floating(make_window("foot", scratchpad_state="shown"))
        self.assertCommand("floating enable")
        self.assertCommand("border normal")
        self.assertCommand("move scratchpad")
        self.assertCommand("scratchpad show")

    def test_plain_floating_window(self):
        self._floating(make_window("foot"))
        self.assertCommand("floating enable")
        self.assertCommand("move position 0 0")
        self.assertNotIn("scratchpad", " ".join(self.calls))

    def test_helium_floating_moved_to_current_workspace(self):
        self._floating(make_window("helium", name="hel tab"))
        self.assertCommand("move to workspace 1")
        self.assertCommand("floating enable")

    def test_fullscreen_floating_window(self):
        self._floating(make_window("foot", fullscreen_mode=1))
        self.assertCommand("fullscreen")

    def test_non_fullscreen_floating_window(self):
        self._floating(make_window("foot", fullscreen_mode=0))
        self.assertNotIn("fullscreen", " ".join(self.calls))

    def test_marks_applied_to_foot_drop_floating(self):
        self._floating(make_window("foot_drop", marks=["d"]))
        self.assertCommand("mark d")

    def test_marks_applied_to_scratchpad_floating(self):
        self._floating(make_window("foot", scratchpad_state="shown", marks=["s"]))
        self.assertCommand("mark s")


class TestApplyGeometry(RestoreHarnessTestCase):
    """Saved rects are output-absolute; `move position` is workspace-relative
    and anchors on the titlebar, so _apply_geometry must convert both."""

    def _tree(self, ws_origin=(4, 28), deco_height=0, win_id=1000):
        tree = self._fake_get_tree()
        tree["nodes"].append(
            {
                "type": "output",
                "name": "eDP-1",
                "active": True,
                "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "nodes": [
                    {
                        "type": "workspace",
                        "name": "1",
                        "rect": {
                            "x": ws_origin[0],
                            "y": ws_origin[1],
                            "width": 1912,
                            "height": 1048,
                        },
                        "nodes": [],
                        "floating_nodes": [
                            {
                                "id": win_id,
                                "deco_rect": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 100,
                                    "height": deco_height,
                                },
                                "nodes": [],
                                "floating_nodes": [],
                            }
                        ],
                    }
                ],
                "floating_nodes": [],
            }
        )
        return tree

    def _apply(self, rect, ws_origin=(4, 28), deco_height=0):
        import unittest.mock

        tree = self._tree(ws_origin, deco_height)
        with unittest.mock.patch.object(self.restore_mod, "get_tree", lambda: tree):
            self.restore_mod._apply_geometry(1000, rect, "1")

    def test_converts_output_to_workspace_coords(self):
        self._apply({"x": 243, "y": 197, "width": 800, "height": 600})
        self.assertCommand("move position 239 169")
        self.assertCommand("resize set width 800 px height 600 px")

    def test_titlebar_added_to_height_and_subtracted_from_y(self):
        self._apply(
            {"x": 243, "y": 197, "width": 1434, "height": 709},
            deco_height=26,
        )
        self.assertCommand("move position 239 143")
        self.assertCommand("resize set width 1434 px height 735 px")

    def test_resize_precedes_move(self):
        self._apply({"x": 243, "y": 197, "width": 800, "height": 600})
        moves = [i for i, c in enumerate(self.calls) if "move position" in c]
        resizes = [i for i, c in enumerate(self.calls) if "resize set" in c]
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(resizes), 1)
        self.assertLess(resizes[0], moves[0])

    def test_missing_workspace_falls_back_to_saved_coords(self):
        import unittest.mock

        with unittest.mock.patch.object(
            self.restore_mod, "get_tree", self._fake_get_tree
        ):
            self.restore_mod._apply_geometry(
                1000, {"x": 10, "y": 20, "width": 800, "height": 600}, "1"
            )
        self.assertCommand("move position 10 20")


class TestHeliumScratchpad(RestoreHarnessTestCase):
    def test_helium_in_hidden_scratchpad_is_restored(self):
        hel = make_window("helium", name="scratch hel tab")
        payload = {
            "workspaces": [],
            "hidden_scratchpad": [hel],
            "background_apps": [],
        }
        ctx = self.restore_workspaces(payload)
        self.assertEqual(len(ctx.helium_saved_nodes), 1)
        self.assertIsNotNone(ctx.helium_restored_ids[0])
        self.assertCommand("floating enable")
        self.assertCommand("move scratchpad")

    def test_helium_scratchpad_plus_workspace_collected_once(self):
        hel_ws = make_window("helium", name="ws hel tab")
        hel_sp = make_window("helium", name="sp hel tab")
        ws = make_workspace("1", nodes=[hel_ws])
        payload = {
            "workspaces": [ws],
            "hidden_scratchpad": [hel_sp],
            "background_apps": [],
        }
        ctx = self.restore_workspaces(payload)
        self.assertEqual(len(ctx.helium_saved_nodes), 2)
        self.assertEqual(len(ctx.helium_restored_ids), 2)

    def test_non_helium_scratchpad_restored_plain(self):
        win = make_window("foot", cwd="/tmp")
        payload = {"workspaces": [], "hidden_scratchpad": [win], "background_apps": []}
        self.restore_workspaces(payload)
        self.assertCommand("floating enable")
        self.assertCommand("border normal")
        self.assertCommand("move scratchpad")


class TestFocusedWorkspace(RestoreHarnessTestCase):
    def _run_locked(self, payload, focused=None):
        """Run _restore_session_locked against a temp state file."""
        import json
        import tempfile
        import unittest.mock
        from contextlib import nullcontext
        from pathlib import Path

        if focused is not None:
            payload["focused_workspace"] = focused
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "sway_session.json"
            state_file.write_text(json.dumps(payload), encoding="utf-8")
            extra = [
                unittest.mock.patch.object(self.restore_mod, "STATE_FILE", state_file),
                unittest.mock.patch.object(
                    self.restore_mod, "operation_lock", lambda _dir: nullcontext()
                ),
                unittest.mock.patch.object(self.restore_mod, "restore_background_apps"),
                unittest.mock.patch.object(self.restore_mod, "close_connection"),
                unittest.mock.patch.object(self.restore_mod, "ProcCache"),
            ]
            for p in extra:
                p.start()
            try:
                self.restore_mod._restore_session_locked(notify_user=False)
            finally:
                for p in extra:
                    p.stop()

    def test_restore_ends_on_focused_workspace(self):
        ws1 = make_workspace("1", nodes=[make_window("foot", cwd="/a")])
        ws3 = make_workspace("3", nodes=[make_window("foot", cwd="/b")])
        payload = {
            "workspaces": [ws1, ws3],
            "hidden_scratchpad": [],
            "background_apps": [],
        }
        self._run_locked(payload, focused="3")
        switches = [c for c in self.calls if c.startswith("workspace ")]
        self.assertEqual(switches[-1], "workspace 3")

    def test_restore_falls_back_to_workspace_1(self):
        ws2 = make_workspace("2", nodes=[make_window("foot", cwd="/a")])
        payload = {"workspaces": [ws2], "hidden_scratchpad": [], "background_apps": []}
        self._run_locked(payload, focused=None)
        switches = [c for c in self.calls if c.startswith("workspace ")]
        self.assertEqual(switches[-1], "workspace 1")

    def test_invalid_session_file_skips_restore(self):
        import tempfile
        import unittest.mock
        from contextlib import nullcontext
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "sway_session.json"
            state_file.write_text("{ not valid json", encoding="utf-8")
            extra = [
                unittest.mock.patch.object(self.restore_mod, "STATE_FILE", state_file),
                unittest.mock.patch.object(
                    self.restore_mod, "operation_lock", lambda _dir: nullcontext()
                ),
                unittest.mock.patch.object(self.restore_mod, "close_connection"),
            ]
            for p in extra:
                p.start()
            try:
                self.restore_mod._restore_session_locked(notify_user=False)
            finally:
                for p in extra:
                    p.stop()
        self.assertEqual(self.calls, [])


class TestHasRestorableContent(RestoreHarnessTestCase):
    def _check(self, content):
        """Point STATE_FILE at a temp file with the given text content."""
        import json
        import tempfile
        import unittest.mock
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "sway_session.json"
            if content is not None:
                if isinstance(content, (dict, list)):
                    content = json.dumps(content)
                state_file.write_text(content, encoding="utf-8")
            with unittest.mock.patch.object(self.restore_mod, "STATE_FILE", state_file):
                return self.restore_mod.has_restorable_content()

    def test_missing_file_is_empty(self):
        self.assertFalse(self._check(None))

    def test_all_empty_lists_is_empty(self):
        payload = {"workspaces": [], "hidden_scratchpad": [], "background_apps": []}
        self.assertFalse(self._check(payload))

    def test_legacy_empty_list_is_empty(self):
        self.assertFalse(self._check([]))

    def test_workspace_counts_as_content(self):
        ws = make_workspace("1", nodes=[make_window("foot")])
        self.assertTrue(self._check({"workspaces": [ws]}))

    def test_scratchpad_window_alone_counts_as_content(self):
        win = make_window("foot")
        payload = {"workspaces": [], "hidden_scratchpad": [win]}
        self.assertTrue(self._check(payload))

    def test_drop_terminal_alone_is_empty(self):
        drop = make_window("foot_drop")
        payload = {"workspaces": [], "hidden_scratchpad": [drop]}
        self.assertFalse(self._check(payload))

    def test_drop_terminal_alongside_real_scratchpad_counts(self):
        drop = make_window("foot_drop")
        win = make_window("foot")
        payload = {"workspaces": [], "hidden_scratchpad": [drop, win]}
        self.assertTrue(self._check(payload))

    def test_background_app_alone_counts_as_content(self):
        payload = {
            "workspaces": [],
            "hidden_scratchpad": [],
            "background_apps": [{"app_id": "vesktop"}],
        }
        self.assertTrue(self._check(payload))

    def test_unreadable_json_is_not_restorable(self):
        self.assertFalse(self._check("{ not valid json"))

    def test_structurally_invalid_payload_is_not_restorable(self):
        self.assertFalse(self._check("not a payload"))


if __name__ == "__main__":
    unittest.main()
