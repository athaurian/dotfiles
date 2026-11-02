"""Tests for background app detection / restoration."""

import json
import os
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
            unittest.mock.patch.object(bg_mod, "_ensure_background_daemons"),
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

    def test_invalid_sidecar_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = Path(tmp) / "background.json"
            sidecar.write_text("{not json", encoding="utf-8")
            with unittest.mock.patch.object(bg_mod, "BACKGROUND_APPS_FILE", sidecar):
                bg_mod.restore_background_apps(None, cache=FakeCache())
        self.assertEqual(self.popen_calls, [])

    def test_non_list_sidecar_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = Path(tmp) / "background.json"
            sidecar.write_text('{"app_id": "vesktop"}', encoding="utf-8")
            with unittest.mock.patch.object(bg_mod, "BACKGROUND_APPS_FILE", sidecar):
                bg_mod.restore_background_apps(None, cache=FakeCache())
        self.assertEqual(self.popen_calls, [])

    def test_non_dict_entries_are_skipped(self):
        bg_mod.restore_background_apps([42], cache=FakeCache())
        self.assertEqual(self.popen_calls, [])

    def test_existing_window_is_not_duplicated(self):
        with unittest.mock.patch.object(
            bg_mod, "matching_window_ids", return_value=[7]
        ):
            bg_mod.restore_background_apps(
                [{"app_id": "vesktop"}], cache=FakeCache(running=False)
            )
        self.assertEqual(self.popen_calls, [])

    def test_launch_failure_is_ignored(self):
        with unittest.mock.patch.object(
            bg_mod.subprocess, "Popen", side_effect=OSError("missing")
        ):
            bg_mod.restore_background_apps(
                [{"app_id": "vesktop"}], cache=FakeCache(running=False)
            )


class TestEnsureBackgroundDaemons(unittest.TestCase):
    def setUp(self):
        env = unittest.mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("SWAY_SESSION_SKIP_DAEMON_CHECKS", None)

    def _run_checks(self, results=None, backend="sway"):
        results = results or {}
        calls = []

        def fake_run(command, **_kwargs):
            calls.append(list(command))
            return unittest.mock.Mock(returncode=results.get(" ".join(command), 0))

        with (
            unittest.mock.patch.object(bg_mod, "detect_backend", return_value=backend),
            unittest.mock.patch.object(bg_mod.subprocess, "run", side_effect=fake_run),
            unittest.mock.patch("session_manager_lib.logging_setup.notify") as notify,
        ):
            bg_mod._ensure_background_daemons()
        return calls, notify

    def test_checks_every_sway_daemon(self):
        calls, notify = self._run_checks()
        checked = {" ".join(call[:3]) for call in calls}
        self.assertIn("pgrep -x swayidle", checked)
        self.assertIn("pgrep -x pipewire", checked)
        self.assertIn("pgrep -x pipewire-pulse", checked)
        notify.assert_not_called()

    def test_restarts_a_missing_sway_daemon(self):
        calls, notify = self._run_checks({"pgrep -x swayidle": 1})
        self.assertIn(["systemctl", "--user", "start", "--no-block", "swayidle"], calls)
        notify.assert_called_once()

    def test_reports_but_does_not_restart_a_missing_xss_lock(self):
        calls, notify = self._run_checks({"pgrep -x xss-lock": 1}, backend="i3")
        self.assertIn(["pgrep", "-x", "xss-lock"], calls)
        self.assertNotIn(
            ["systemctl", "--user", "start", "--no-block", "xss-lock"], calls
        )
        notify.assert_called_once()

    def test_starts_an_inactive_session_target(self):
        calls, notify = self._run_checks(
            {"systemctl --user is-active --quiet sway-session.target": 1}
        )
        self.assertIn(
            ["systemctl", "--user", "start", "--no-block", "sway-session.target"],
            calls,
        )
        notify.assert_called_once()

    def test_skips_checks_when_opted_out(self):
        with (
            unittest.mock.patch.dict(
                os.environ, {"SWAY_SESSION_SKIP_DAEMON_CHECKS": "1"}
            ),
            unittest.mock.patch.object(bg_mod.subprocess, "run") as run,
        ):
            bg_mod._ensure_background_daemons()
        run.assert_not_called()

    def test_skips_checks_when_launches_are_mocked(self):
        with (
            unittest.mock.patch.object(bg_mod.subprocess, "Popen", object()),
            unittest.mock.patch.object(bg_mod.subprocess, "run") as run,
        ):
            bg_mod._ensure_background_daemons()
        run.assert_not_called()

    def test_subprocess_failures_are_ignored(self):
        with unittest.mock.patch.object(
            bg_mod.subprocess, "run", side_effect=OSError("missing")
        ):
            bg_mod._ensure_background_daemons()


if __name__ == "__main__":
    unittest.main()
