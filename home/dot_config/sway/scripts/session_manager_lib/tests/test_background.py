"""Tests for background app detection / restoration."""

import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.background as bg_mod


class FakeCache:
    def __init__(self, running: bool = False):
        self.running = running
        self.snapshot_calls = 0

    def process_named_running(self, name):
        return self.running


class TestDetectBackgroundApps(unittest.TestCase):
    def test_running_without_window_detected(self):
        with unittest.mock.patch.object(
            bg_mod, "matching_window_ids_in_tree", return_value=[]
        ):
            result = bg_mod.detect_background_apps(FakeCache(running=True), tree={})
        self.assertEqual(result, [{"app_id": "vesktop"}])

    def test_running_with_window_not_detected(self):
        with unittest.mock.patch.object(
            bg_mod, "matching_window_ids_in_tree", return_value=[42]
        ):
            result = bg_mod.detect_background_apps(FakeCache(running=True), tree={})
        self.assertEqual(result, [])

    def test_not_running_not_detected(self):
        with unittest.mock.patch.object(
            bg_mod, "matching_window_ids_in_tree", return_value=[]
        ):
            result = bg_mod.detect_background_apps(FakeCache(running=False), tree={})
        self.assertEqual(result, [])


class TestRestoreBackgroundApps(unittest.TestCase):
    def setUp(self):
        self.popen_calls = []

        def fake_popen(cmd, **kw):
            self.popen_calls.append(cmd)
            return unittest.mock.Mock()

        self.patches = [
            unittest.mock.patch.object(bg_mod, "matching_window_ids", return_value=[]),
            unittest.mock.patch.object(bg_mod.subprocess, "Popen", fake_popen),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_launches_when_absent(self):
        bg_mod.restore_background_apps(
            [{"app_id": "vesktop"}], cache=FakeCache(running=False)
        )
        self.assertEqual(len(self.popen_calls), 1)
        self.assertIn("--start-minimized", self.popen_calls[0])

    def test_skips_when_process_running(self):
        bg_mod.restore_background_apps(
            [{"app_id": "vesktop"}], cache=FakeCache(running=True)
        )
        self.assertEqual(self.popen_calls, [])

    def test_skips_non_vesktop(self):
        bg_mod.restore_background_apps([{"app_id": "other"}], cache=None)
        self.assertEqual(self.popen_calls, [])

    def test_no_snapshot_when_no_apps(self):
        with unittest.mock.patch.object(bg_mod, "ProcCache") as proc_cache_cls:
            bg_mod.restore_background_apps([], cache=None)
        proc_cache_cls.snapshot.assert_not_called()

    def test_snapshot_taken_lazily(self):
        with unittest.mock.patch.object(bg_mod, "ProcCache") as proc_cache_cls:
            proc_cache_cls.snapshot.return_value = FakeCache(running=True)
            bg_mod.restore_background_apps([{"app_id": "vesktop"}], cache=None)
        proc_cache_cls.snapshot.assert_called_once()

    def test_none_reads_sidecar_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = Path(tmp) / "background.json"
            sidecar.write_text(json.dumps([{"app_id": "vesktop"}]), encoding="utf-8")
            with unittest.mock.patch.object(bg_mod, "BACKGROUND_APPS_FILE", sidecar):
                bg_mod.restore_background_apps(None, cache=FakeCache(running=False))
        self.assertEqual(len(self.popen_calls), 1)


if __name__ == "__main__":
    unittest.main()
