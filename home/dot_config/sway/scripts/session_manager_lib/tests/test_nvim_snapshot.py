"""Tests for manager-owned Neovim snapshots."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.nvim.snapshot as snapshot_mod


class TestSnacksSidecarPath(unittest.TestCase):
    def test_appends_a_suffix_to_the_snapshot(self):
        self.assertEqual(
            snapshot_mod.snacks_sidecar_path(Path("/tmp/session.vim")),
            Path("/tmp/session.vim.snacks"),
        )


class CreateSnapshotTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.snapshot = Path(self.tmp.name) / "session.vim"

    def create(self, result, removed=0):
        with (
            unittest.mock.patch.object(
                snapshot_mod, "nvim_rpc", return_value=result
            ) as rpc,
            unittest.mock.patch.object(
                snapshot_mod, "cleanup_stale_swapfiles", return_value=removed
            ) as cleanup,
        ):
            outcome = snapshot_mod.create_manager_snapshot(
                "/tmp/nvim.sock", self.snapshot, 123
            )
        return outcome, rpc, cleanup


class TestCreateManagerSnapshot(CreateSnapshotTestCase):
    def test_rpc_failure_is_reported(self):
        outcome, _, cleanup = self.create(None)
        self.assertEqual(outcome, (False, "RPC failed"))
        cleanup.assert_not_called()

    def test_session_command_failure_is_reported(self):
        outcome, _, _ = self.create(
            {"snapshot_ok": False, "snapshot_error": "E123: failed"}
        )
        self.assertEqual(outcome, (False, "E123: failed"))

    def test_missing_snapshot_file_is_reported(self):
        outcome, _, _ = self.create({"snapshot_ok": True})
        self.assertEqual(outcome, (False, "Snapshot file missing after mksession"))

    def test_successful_snapshot_cleans_stale_swaps(self):
        self.snapshot.write_text("set number\n", encoding="utf-8")
        outcome, rpc, cleanup = self.create(
            {"snapshot_ok": True, "snacks_explorer_open": 1}, removed=2
        )
        self.assertEqual(outcome, (True, None))
        cleanup.assert_called_once_with(self.snapshot)
        self.assertEqual(rpc.call_args.args[0], "/tmp/nvim.sock")
        self.assertEqual(rpc.call_args.args[2], "snapshot_ok")

    def test_unreadable_snapshot_is_reported(self):
        self.snapshot.write_text("set number\n", encoding="utf-8")
        with unittest.mock.patch.object(
            Path, "read_text", side_effect=OSError("permission denied")
        ):
            outcome, _, _ = self.create({"snapshot_ok": True})
        self.assertEqual(outcome, (False, "Unreadable snapshot: permission denied"))


if __name__ == "__main__":
    unittest.main()
