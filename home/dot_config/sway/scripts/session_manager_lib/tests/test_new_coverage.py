"""New coverage for helpers introduced/cleaned in refactor."""

import os
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.config as cfg_mod
from session_manager_lib.apps._common import normalize_title, reap_if_needed
from session_manager_lib.nvim.sockets import nvim_socket_path, runtime_dir


class TestEscapeCwd(unittest.TestCase):
    def test_forward_slash(self):
        self.assertEqual(cfg_mod.escape_cwd("/home/user/proj"), "%home%user%proj")

    def test_mixed_separators(self):
        self.assertEqual(cfg_mod.escape_cwd("C:\\Windows\\a:b/c"), "C%Windows%a%b%c")

    def test_already_percent_preserved(self):
        # Existing % not escaped, just slashes replaced
        self.assertEqual(cfg_mod.escape_cwd("/a%b/c"), "%a%b%c")


class TestNormalizeTitle(unittest.TestCase):
    def test_strip_and_lower(self):
        self.assertEqual(normalize_title("  Hello World  "), "hello world")

    def test_collapse_whitespace(self):
        self.assertEqual(normalize_title("Tab\t  A\nB"), "tab a b")
        self.assertEqual(normalize_title("  Tab   A  "), "tab a")

    def test_empty(self):
        self.assertEqual(normalize_title("   "), "")

    def test_matches_helium_early_reuse(self):
        self.assertEqual(normalize_title("Tab  A"), normalize_title("tab a"))


class TestReapIfNeeded(unittest.TestCase):
    def test_reaps_when_exited(self):
        mock_proc = unittest.mock.Mock()
        mock_proc.poll.return_value = 0
        reap_if_needed(mock_proc)
        mock_proc.wait.assert_called_once_with(timeout=0)

    def test_noop_when_running(self):
        mock_proc = unittest.mock.Mock()
        mock_proc.poll.return_value = None
        reap_if_needed(mock_proc)
        mock_proc.wait.assert_not_called()

    def test_noop_when_none(self):
        # Should not raise
        reap_if_needed(None)

    def test_swallows_wait_error(self):
        mock_proc = unittest.mock.Mock()
        mock_proc.poll.return_value = 1
        mock_proc.wait.side_effect = OSError("gone")
        reap_if_needed(mock_proc)  # no raise

        mock_proc2 = unittest.mock.Mock()
        mock_proc2.poll.return_value = 1
        mock_proc2.wait.side_effect = subprocess.TimeoutExpired("cmd", 0)
        reap_if_needed(mock_proc2)

    def test_swallows_poll_error(self):
        # The try/except wraps both poll() and wait(), so OSError from
        # either call is swallowed to avoid zombie processes.
        mock_proc = unittest.mock.Mock()
        mock_proc.poll.side_effect = OSError("bad")
        reap_if_needed(mock_proc)  # should not raise


class TestConfigXdgAndConstants(unittest.TestCase):
    def test_xdg_dir_helper(self):
        with unittest.mock.patch.dict(os.environ, {"XDG_STATE_HOME": "/tmp/xdg_state"}):
            self.assertEqual(
                cfg_mod._xdg_dir("XDG_STATE_HOME", Path("/fallback")),
                Path("/tmp/xdg_state"),
            )
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            # ensure fallback used when var absent
            if "XDG_STATE_HOME" in os.environ:
                del os.environ["XDG_STATE_HOME"]
            # can't easily test without env, just check fallback path
            self.assertEqual(
                cfg_mod._xdg_dir("XDG_STATE_HOME", Path("/fallback")), Path("/fallback")
            )

    def test_default_geometry_constants(self):
        self.assertEqual(cfg_mod.DEFAULT_WINDOW_WIDTH, 800)
        self.assertEqual(cfg_mod.DEFAULT_WINDOW_HEIGHT, 600)

    def test_scratch_constants(self):
        self.assertEqual(cfg_mod.SCRATCHPAD_WORKSPACE, "__i3_scratch")
        self.assertEqual(cfg_mod.SCRATCH_RESTORE_WORKSPACE, "__scratch_restore")

    def test_app_profile_typed(self):
        self.assertIn("helium", cfg_mod.APP_PROFILES)
        self.assertEqual(cfg_mod.APP_PROFILES["helium"]["timeout"], 30.0)
        self.assertIsInstance(cfg_mod.DEFAULT_APP_PROFILE["settle"], float)


class TestNvimSockets(unittest.TestCase):
    def test_runtime_dir_uses_env(self):
        with unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/tmp/run"}):
            self.assertEqual(runtime_dir(), Path("/tmp/run"))
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            # fallback to /run/user/<uid>
            if "XDG_RUNTIME_DIR" in os.environ:
                del os.environ["XDG_RUNTIME_DIR"]
            rd = runtime_dir()
            self.assertTrue(str(rd).startswith("/run/user/"))

    def test_nvim_socket_path(self):
        with unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/tmp/run"}):
            self.assertEqual(nvim_socket_path(1234), Path("/tmp/run/nvim.1234.0"))
        # fallback
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            if "XDG_RUNTIME_DIR" in os.environ:
                del os.environ["XDG_RUNTIME_DIR"]
            p = nvim_socket_path(99)
            self.assertEqual(p.name, "nvim.99.0")

    def test_snapshot_path_uses_escape(self):
        from session_manager_lib.nvim.snapshot import get_nvim_snapshot_path

        with (
            tempfile.TemporaryDirectory() as tmp,
            unittest.mock.patch.object(cfg_mod, "STATE_DIR", Path(tmp)),
        ):
            p = get_nvim_snapshot_path("/home/user/proj", pid=42)
            self.assertIn("%home%user%proj%42", str(p))
            self.assertTrue(str(p).endswith(".vim"))


class TestRestoreHelpers(unittest.TestCase):
    def _harness(self):
        from session_manager_lib.tests.helpers import RestoreHarnessTestCase

        class Dummy(RestoreHarnessTestCase):
            def test_dummy(self):
                pass

        tc = Dummy("test_dummy")
        tc.setUp()
        return tc

    def test_apply_geometry_uses_defaults(self):
        harness = self._harness()
        try:
            # Missing rect should still produce default width/height
            from session_manager_lib.tests.helpers import make_window, make_workspace

            win = make_window("foot", rect={})
            ws = make_workspace("1", floating=[win])
            harness.restore_workspaces({"workspaces": [ws]})
            # Check that default 800/600 appear
            self.assertTrue(any("800 px" in c for c in harness.calls))
            self.assertTrue(any("600 px" in c for c in harness.calls))
        finally:
            harness.tearDown()

    def test_split_orientation(self):
        from session_manager_lib.tests.helpers import (
            make_con,
            make_window,
            make_workspace,
        )

        harness = self._harness()
        try:
            # splitv layout should produce split v
            con = make_con(
                nodes=[make_window("foot"), make_window("foot")], layout="splitv"
            )
            ws = make_workspace("1", nodes=[con])
            harness.restore_workspaces({"workspaces": [ws]})
            self.assertIn("split v", harness.calls)
            self.assertIn("layout splitv", harness.calls)

            harness.calls.clear()
            # splith layout should produce split h
            con2 = make_con(
                nodes=[make_window("foot"), make_window("foot")], layout="splith"
            )
            ws2 = make_workspace("1", nodes=[con2])
            harness.restore_workspaces({"workspaces": [ws2]})
            self.assertIn("split h", harness.calls)
        finally:
            harness.tearDown()


if __name__ == "__main__":
    unittest.main()
