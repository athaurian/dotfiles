"""Tests for restore orchestration: payload normalisation, focused-workspace,
and floating-window restore branches."""

import unittest
import unittest.mock

from session_manager_lib.tests.helpers import (
    RestoreHarnessTestCase,
    make_con,
    make_two_output_tree,
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
        payload = {"workspaces": [make_window("kitty")]}
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm(payload)

    def test_missing_layout_rejected(self):
        ws = make_workspace("1")
        del ws["layout"]
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})

    def test_invalid_mark_types_rejected(self):
        win = make_window("kitty", marks=[42])
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})


class TestRestoreNode(RestoreHarnessTestCase):
    def test_workspace_restores_tiled_and_floating_children(self):
        win = make_window("kitty", cwd="/tmp")
        ws = make_workspace(
            "1", nodes=[win], floating=[make_window("kitty", cwd="/tmp")]
        )
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("workspace 1")
        self.assertCommand("[con_id=1000] focus")
        self.assertCommand("[con_id=1001] floating enable")

    def test_con_with_only_floating_children(self):
        con = make_con(nodes=[], floating=[make_window("kitty", cwd="/tmp")])
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
        win_a = make_window("kitty", cwd="/a")
        win_b = make_window("kitty", cwd="/b")
        con = make_con(nodes=[win_a, win_b], layout="tabbed")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertIn("split h", self.calls)
        self.assertIn("layout tabbed", self.calls)
        ids = [c for c in self.calls if c.startswith("[con_id=")]
        self.assertEqual(len(ids), 2)

    def test_con_splitv_uses_split_v(self):
        win_a = make_window("kitty", cwd="/a")
        win_b = make_window("kitty", cwd="/b")
        con = make_con(nodes=[win_a, win_b], layout="splitv")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertIn("split v", self.calls)
        self.assertIn("layout splitv", self.calls)

    def test_marks_applied_to_restored_window(self):
        win = make_window("kitty", marks=["foo", "bar"])
        ws = make_workspace("1", nodes=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("mark foo")
        self.assertCommand("mark bar")


class TestRestoreFloating(RestoreHarnessTestCase):
    def _floating(self, node):
        ws = make_workspace("1", floating=[node])
        return self.restore_workspaces({"workspaces": [ws]})

    def test_kitty_drop_only_geometry(self):
        self._floating(make_window("kitty_drop"))
        self.assertCommand("move position 0 0")
        self.assertCommand("resize set width 800 px")
        joined = " ".join(self.calls)
        self.assertNotIn("floating enable", joined)
        self.assertNotIn("border normal", joined)
        self.assertNotIn("scratchpad", joined)

    def test_scratchpad_window_moved_to_scratchpad(self):
        self._floating(make_window("kitty", scratchpad_state="shown"))
        self.assertCommand("floating enable")
        self.assertCommand("border normal")
        self.assertCommand("move scratchpad")
        self.assertCommand("scratchpad show")

    def test_plain_floating_window(self):
        self._floating(make_window("kitty"))
        self.assertCommand("floating enable")
        self.assertCommand("move position 0 0")
        self.assertNotIn("scratchpad", " ".join(self.calls))

    def test_helium_floating_moved_to_current_workspace(self):
        self._floating(make_window("helium", name="hel tab"))
        self.assertCommand("move to workspace 1")
        self.assertCommand("floating enable")

    def test_fullscreen_floating_window(self):
        self._floating(make_window("kitty", fullscreen_mode=1))
        self.assertCommand("fullscreen")

    def test_non_fullscreen_floating_window(self):
        self._floating(make_window("kitty", fullscreen_mode=0))
        self.assertNotIn("fullscreen", " ".join(self.calls))

    def test_marks_applied_to_kitty_drop_floating(self):
        self._floating(make_window("kitty_drop", marks=["d"]))
        self.assertCommand("mark d")

    def test_marks_applied_to_scratchpad_floating(self):
        self._floating(make_window("kitty", scratchpad_state="shown", marks=["s"]))
        self.assertCommand("mark s")


class TestApplyGeometry(RestoreHarnessTestCase):
    """Saved rects are output-absolute. `move position` is workspace-relative
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
        self.assertEqual(len(moves), 2)
        self.assertEqual(len(resizes), 2)
        self.assertLess(resizes[0], moves[0])
        self.assertLess(resizes[1], moves[1])

    def test_geometry_is_applied_again_after_the_window_settles(self):
        """Sway lets a new window ask for its own size, and that request
        lands after the first resize and undoes it. The geometry is applied
        a second time so the restored size wins."""
        self._apply({"x": 243, "y": 197, "width": 800, "height": 600})
        resizes = [c for c in self.calls if "resize set" in c]
        moves = [c for c in self.calls if "move position" in c]
        self.assertEqual(
            resizes[0], "[con_id=1000] resize set width 800 px height 600 px"
        )
        self.assertEqual(resizes[1], resizes[0])
        self.assertEqual(moves[0], "[con_id=1000] move position 239 169")
        self.assertEqual(moves[1], moves[0])

    def test_retry_measures_the_titlebar_that_appeared_after_the_launch(self):
        """A window that has just started has no titlebar yet, so the first
        attempt cannot measure its height. The retry re-measures it."""
        import unittest.mock

        trees = [
            self._tree(deco_height=0),
            self._tree(deco_height=21),
        ]
        # Each geometry application reads the tree twice: once for the
        # titlebar height and once for the workspace origin.
        seen: list[int] = []

        def fake_tree():
            seen.append(1)
            return trees[0] if len(seen) <= 2 else trees[1]

        with unittest.mock.patch.object(self.restore_mod, "get_tree", fake_tree):
            self.restore_mod._apply_geometry(
                1000, {"x": 243, "y": 197, "width": 800, "height": 600}, "1"
            )
        resizes = [c for c in self.calls if "resize set" in c]
        moves = [c for c in self.calls if "move position" in c]
        # First attempt: no titlebar yet.
        self.assertEqual(
            resizes[0], "[con_id=1000] resize set width 800 px height 600 px"
        )
        # Retry: the titlebar is 21px, so it is added to the height and
        # subtracted from the y position.
        self.assertEqual(
            resizes[1], "[con_id=1000] resize set width 800 px height 621 px"
        )
        self.assertEqual(moves[1], "[con_id=1000] move position 239 148")

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
        win = make_window("kitty", cwd="/tmp")
        payload = {"workspaces": [], "hidden_scratchpad": [win], "background_apps": []}
        self.restore_workspaces(payload)
        self.assertCommand("floating enable")
        self.assertCommand("border normal")
        self.assertCommand("move scratchpad")


class TestFocusedWorkspace(RestoreHarnessTestCase):
    def _run_locked(self, payload, focused=None):
        """Runs _restore_session_locked against a temp state file."""
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
        ws1 = make_workspace("1", nodes=[make_window("kitty", cwd="/a")])
        ws3 = make_workspace("3", nodes=[make_window("kitty", cwd="/b")])
        payload = {
            "workspaces": [ws1, ws3],
            "hidden_scratchpad": [],
            "background_apps": [],
        }
        self._run_locked(payload, focused="3")
        switches = [c for c in self.calls if c.startswith("workspace ")]
        self.assertEqual(switches[-1], "workspace 3")

    def test_restore_falls_back_to_workspace_1(self):
        ws2 = make_workspace("2", nodes=[make_window("kitty", cwd="/a")])
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
        ws = make_workspace("1", nodes=[make_window("kitty")])
        self.assertTrue(self._check({"workspaces": [ws]}))

    def test_scratchpad_window_alone_counts_as_content(self):
        win = make_window("kitty")
        payload = {"workspaces": [], "hidden_scratchpad": [win]}
        self.assertTrue(self._check(payload))

    def test_drop_terminal_alone_is_empty(self):
        drop = make_window("kitty_drop")
        payload = {"workspaces": [], "hidden_scratchpad": [drop]}
        self.assertFalse(self._check(payload))

    def test_drop_terminal_alongside_real_scratchpad_counts(self):
        drop = make_window("kitty_drop")
        win = make_window("kitty")
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


class TestPayloadValidation(RestoreHarnessTestCase):
    """A malformed payload must be refused before anything is launched."""

    def _norm(self, payload):
        return self.restore_mod._normalise_restore_payload(payload)

    def test_rect_members_must_be_numbers(self):
        win = make_window(
            "kitty",
            rect={"x": 0, "y": 0, "width": "800 px; exec id", "height": 600},
        )
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})

    def test_rect_members_must_be_finite(self):
        win = make_window(
            "kitty", rect={"x": 0, "y": 0, "width": float("inf"), "height": 600}
        )
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})

    def test_percent_must_be_finite(self):
        win = make_window("kitty", percent=float("nan"))
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})

    def test_null_rect_member_is_refused(self):
        win = make_window(
            "kitty", rect={"x": None, "y": 0, "width": 800, "height": 600}
        )
        ws = make_workspace("1", nodes=[win])
        with self.assertRaises(self.restore_mod.StateValidationError):
            self._norm({"workspaces": [ws]})


class TestCommandSafety(RestoreHarnessTestCase):
    """Saved values must never become extra compositor commands."""

    def test_unsafe_mark_is_skipped(self):
        win = make_window("kitty", marks=["ok", "a; exec id"])
        ws = make_workspace("1", nodes=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("mark ok")
        self.assertNotIn("exec id", " ".join(self.calls))

    def test_unknown_layout_is_skipped(self):
        con = make_con(nodes=[make_window("kitty")], layout="totally-bogus")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertNotIn("totally-bogus", " ".join(self.calls))

    def test_stacked_layout_is_sent_as_stacking(self):
        con = make_con(nodes=[make_window("kitty")], layout="stacked")
        ws = make_workspace("1", nodes=[con])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("layout stacking")

    def test_geometry_uses_plain_numbers(self):
        # The payload check refuses this rect; the geometry code must also
        # survive it when it is called directly.
        self.restore_mod._apply_geometry(
            1000,
            {"x": "10; exec id", "y": 0, "width": 800, "height": 600},
            "1",
        )
        joined = " ".join(self.calls)
        self.assertNotIn("exec id", joined)
        self.assertCommand("move position 0 0")
        self.assertCommand("resize set width 800 px height 600 px")

    def test_workspace_name_is_quoted_when_it_has_separators(self):
        ws = make_workspace("2 dev; exec id")
        win = make_window("helium")
        ws["nodes"].append(win)
        self.restore_workspaces({"workspaces": [ws]})
        joined = " ".join(self.calls)
        self.assertIn('workspace "2 dev; exec id"', joined)
        self.assertIn('move to workspace "2 dev; exec id"', joined)


class TestScratchpadBorder(RestoreHarnessTestCase):
    def test_floating_scratchpad_keeps_its_border(self):
        win = make_window("kitty", scratchpad_state="shown", border="pixel")
        ws = make_workspace("1", floating=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("border pixel")
        self.assertNotIn("border normal", " ".join(self.calls))

    def test_scratchpad_without_a_border_falls_back_to_normal(self):
        win = make_window("kitty", scratchpad_state="shown")
        ws = make_workspace("1", floating=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("border normal")


class TestFailureIsolation(RestoreHarnessTestCase):
    """One app that cannot start must not cost the other windows."""

    def _flaky_launch(self):
        state = {"calls": 0}

        def launch(node, claimed_ids):
            state["calls"] += 1
            if state["calls"] == 1:
                raise FileNotFoundError("mpv: command not found")
            win_id = next(self._id_iter)
            claimed_ids.add(win_id)
            return win_id

        return launch

    def test_failing_tiled_window_does_not_stop_the_others(self):
        win_a = make_window("mpv")
        win_b = make_window("kitty")
        ws = make_workspace("1", nodes=[win_a, win_b])
        with unittest.mock.patch.object(
            self.restore_mod, "launch_and_get_id", self._flaky_launch()
        ):
            ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertEqual(len(ctx.failures), 1)
        self.assertIn("mpv", ctx.failures[0])
        self.assertEqual(len(ctx.claimed_ids), 1)
        self.assertCommand("[con_id=1000] focus")

    def test_failing_floating_window_does_not_stop_the_others(self):
        float_a = make_window("mpv")
        float_b = make_window("kitty")
        ws = make_workspace("1", floating=[float_a, float_b])
        with unittest.mock.patch.object(
            self.restore_mod, "launch_and_get_id", self._flaky_launch()
        ):
            ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertEqual(len(ctx.failures), 1)
        self.assertEqual(len(ctx.claimed_ids), 1)

    def test_window_that_does_not_come_back_is_reported(self):
        def no_launch(node, claimed_ids):
            return None

        win = make_window("definitely-not-installed")
        ws = make_workspace("1", nodes=[win])
        with unittest.mock.patch.object(
            self.restore_mod, "launch_and_get_id", no_launch
        ):
            ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertEqual(ctx.missing, ["definitely-not-installed window"])

    def test_drop_terminal_is_not_reported_as_missing(self):
        """The dropdown terminal is spawned by its keybinding on demand."""

        def no_launch(node, claimed_ids):
            return None

        win = make_window("kitty_drop")
        ws = make_workspace("1", nodes=[win])
        with unittest.mock.patch.object(
            self.restore_mod, "launch_and_get_id", no_launch
        ):
            ctx = self.restore_workspaces({"workspaces": [ws]})
        self.assertEqual(ctx.missing, [])


class TestDefaultGeometry(RestoreHarnessTestCase):
    def test_missing_rect_uses_the_default_size(self):
        win = make_window("kitty", rect={})
        ws = make_workspace("1", floating=[win])
        self.restore_workspaces({"workspaces": [ws]})
        self.assertCommand("width 800 px")
        self.assertCommand("height 600 px")


class TestMultiOutputClamp(RestoreHarnessTestCase):
    """A floating window is clamped against the output it was saved on."""

    def _apply(self, rect):
        with unittest.mock.patch.object(
            self.restore_mod, "get_tree", make_two_output_tree
        ):
            self.restore_mod._apply_geometry(1000, rect, "1")

    def test_rect_on_the_second_output_is_not_pulled_to_the_first(self):
        self._apply({"x": 2000, "y": 100, "width": 800, "height": 600})
        self.assertCommand("move position 2000 100")

    def test_rect_beyond_every_output_is_clamped_inwards(self):
        self._apply({"x": 5000, "y": 100, "width": 800, "height": 600})
        self.assertCommand("move position 1120 100")


if __name__ == "__main__":
    unittest.main()
