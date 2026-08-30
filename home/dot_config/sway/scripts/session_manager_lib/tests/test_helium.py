"""Tests for the helium group restore logic: guard semantics and the
event-driven title assignment loop.
"""

import unittest
import unittest.mock
from types import SimpleNamespace

import session_manager_lib.apps.helium as helium_mod
from session_manager_lib.state import RestoreContext
from session_manager_lib.tests.helpers import make_window


class FakePopen:
    pid = 4242
    on_launch = None

    def __init__(self, *args, **kwargs):
        self.args = args
        FakePopen.instances.append(self)
        if FakePopen.on_launch is not None:
            FakePopen.on_launch()

    def poll(self):
        return None


class ScriptedWatcher:
    """WindowEventWatcher stand-in returning scripted events."""

    def __init__(self, events):
        self.events = list(events)
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def get(self, timeout):
        if self.events:
            return self.events.pop(0)
        return None

    def close(self):
        self.closed = True


def ev(change, cid, app_id="helium", name=""):
    return SimpleNamespace(
        change=change,
        container={"id": cid, "app_id": app_id, "name": name, "type": "con"},
    )


def helium_node(cid, name):
    return {
        "id": cid,
        "type": "con",
        "app_id": "helium",
        "name": name,
    }


class HeliumTestCase(unittest.TestCase):
    def setUp(self):
        self.tree_windows: list[dict] = []
        FakePopen.instances = []
        FakePopen.on_launch = None
        self.watcher_events: list = []
        self.patches = [
            unittest.mock.patch.object(helium_mod, "get_tree", self._fake_get_tree),
            unittest.mock.patch.object(
                helium_mod, "WindowEventWatcher", self._fake_watcher_cls
            ),
            unittest.mock.patch.object(helium_mod.subprocess, "Popen", FakePopen),
            unittest.mock.patch.object(helium_mod, "_suppress_helium_crash_prompt"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        FakePopen.on_launch = None
        for p in self.patches:
            p.stop()

    def _fake_get_tree(self):
        return {"nodes": [{"type": "output", "nodes": self.tree_windows}]}

    def _fake_watcher_cls(self, sock_path=None):
        return ScriptedWatcher(self.watcher_events)

    def run_group(self, saved_nodes):
        ctx = RestoreContext()
        for node in saved_nodes:
            ctx.helium_saved_nodes.append(node)
            ctx.helium_saved_index[id(node)] = len(ctx.helium_saved_index)
            ctx.helium_restored_ids.append(None)
        return ctx, helium_mod._restore_helium_group(ctx)


class TestHeliumGuard(HeliumTestCase):
    def test_starts_and_launches_with_saved_nodes(self):
        self.watcher_events = [ev("new", 71, name="tab a")]
        ctx, _ = self.run_group([make_window("helium", name="tab a")])
        self.assertTrue(ctx.helium_restore_started)
        self.assertEqual(len(FakePopen.instances), 1)

    def test_sets_started_without_saved_nodes(self):
        ctx = RestoreContext()
        helium_mod._restore_helium_group(ctx)
        self.assertTrue(ctx.helium_restore_started)
        self.assertEqual(len(FakePopen.instances), 0)

    def test_second_call_is_noop(self):
        self.watcher_events = [ev("new", 72, name="tab a")]
        ctx, _ = self.run_group([make_window("helium", name="tab a")])
        launches = len(FakePopen.instances)
        helium_mod._restore_helium_group(ctx)
        self.assertEqual(len(FakePopen.instances), launches)


class TestHeliumAssignment(HeliumTestCase):
    def _populate_on_launch(self, windows):
        """Populate the fake tree only when the browser process launches."""
        FakePopen.on_launch = lambda: self.tree_windows.extend(windows)

    def test_exact_title_match_from_events(self):
        saved = [
            make_window("helium", name="Tab A"),
            make_window("helium", name="Tab B"),
        ]
        self.watcher_events = [
            ev("new", 11, name=""),
            ev("new", 12, name=""),
            ev("title", 11, name="Tab A"),
            ev("title", 12, name="Tab B"),
        ]
        self._populate_on_launch([helium_node(11, ""), helium_node(12, "")])

        ctx, _ = self.run_group(saved)
        self.assertEqual(ctx.helium_restored_ids, [11, 12])

    def test_event_driven_matching_without_sleep(self):
        saved = [make_window("helium", name=f"Tab {i}") for i in range(3)]
        self._populate_on_launch([helium_node(cid, "") for cid in (21, 22, 23)])
        self.watcher_events = [
            ev("new", 21, name=""),
            ev("new", 22, name=""),
            ev("new", 23, name=""),
            ev("title", 21, name="Tab 0"),
            ev("title", 22, name="Tab 1"),
            ev("title", 23, name="Tab 2"),
        ]

        ctx, _ = self.run_group(saved)
        self.assertEqual(sorted(ctx.helium_restored_ids), [21, 22, 23])

    def test_tree_scan_fallback_matches_titles(self):
        """If title events are missed, the periodic tree scan still assigns."""
        saved = [make_window("helium", name="Only Tab")]
        self.watcher_events = [ev("new", 31, name="")]
        self._populate_on_launch([helium_node(31, "Only Tab")])

        ctx, _ = self.run_group(saved)
        self.assertEqual(ctx.helium_restored_ids, [31])

    def test_close_event_drops_unassigned_window(self):
        saved = [make_window("helium", name="Tab A")]
        self.watcher_events = [
            ev("new", 41, name=""),
            ev("close", 41, name=""),
        ]

        ctx, _ = self.run_group(saved)
        self.assertIsNone(ctx.helium_restored_ids[0])

    def test_fallback_positional_assignment_after_deadline(self):
        """Unmatched titles degrade to positional assignment at deadline."""
        saved = [make_window("helium", name="Wanted Title")]
        self.watcher_events = [ev("new", 51, name="Something Else")]
        self._populate_on_launch([helium_node(51, "Something Else")])

        profile = helium_mod.APP_PROFILES["helium"]
        with unittest.mock.patch.dict(profile, {"timeout": 0.05}):
            ctx, _ = self.run_group(saved)
        self.assertEqual(ctx.helium_restored_ids, [51])


class TestHeliumEarlyReuse(HeliumTestCase):
    def test_reuses_existing_windows_without_launch(self):
        saved = [
            make_window("helium", name="Tab A"),
            make_window("helium", name="Tab B"),
        ]
        # Baseline already has 2 helium windows with matching titles
        self.tree_windows = [helium_node(91, "Tab A"), helium_node(92, "Tab B")]

        mock_cache = unittest.mock.Mock()
        mock_cache.process_named_running.return_value = True

        with unittest.mock.patch.object(
            helium_mod.ProcCache, "snapshot", return_value=mock_cache
        ):
            ctx = RestoreContext()
            for node in saved:
                ctx.helium_saved_nodes.append(node)
                ctx.helium_saved_index[id(node)] = len(ctx.helium_saved_index)
                ctx.helium_restored_ids.append(None)
            helium_mod._restore_helium_group(ctx)

        self.assertEqual(len(FakePopen.instances), 0)
        self.assertEqual(sorted(ctx.helium_restored_ids), [91, 92])

    def test_normalised_title_match_in_early_reuse(self):
        saved = [make_window("helium", name="Tab  A")]
        self.tree_windows = [helium_node(93, "tab a")]

        mock_cache = unittest.mock.Mock()
        mock_cache.process_named_running.return_value = True

        with unittest.mock.patch.object(
            helium_mod.ProcCache, "snapshot", return_value=mock_cache
        ):
            ctx = RestoreContext()
            ctx.helium_saved_nodes.append(saved[0])
            ctx.helium_saved_index[id(saved[0])] = 0
            ctx.helium_restored_ids.append(None)
            helium_mod._restore_helium_group(ctx)

        self.assertEqual(ctx.helium_restored_ids, [93])


class TestHeliumResolve(HeliumTestCase):
    def test_get_restored_id_uses_saved_index(self):
        node = make_window("helium", name="Tab A")
        self.watcher_events = [ev("new", 61, name="Tab A")]
        ctx = RestoreContext()
        ctx.helium_saved_nodes.append(node)
        ctx.helium_saved_index[id(node)] = 0
        ctx.helium_restored_ids.append(None)

        rid = helium_mod.get_helium_restored_id(node, ctx)
        self.assertEqual(rid, 61)

    def test_unknown_node_returns_none(self):
        ctx = RestoreContext()
        self.assertIsNone(helium_mod.get_helium_restored_id({}, ctx))


if __name__ == "__main__":
    unittest.main()
