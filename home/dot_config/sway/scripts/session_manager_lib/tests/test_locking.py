"""Tests for the interprocess operation lock."""

import tempfile
import unittest
from pathlib import Path

from session_manager_lib.config import LOCK_FILE_NAME
from session_manager_lib.locking import operation_lock


class TestOperationLock(unittest.TestCase):
    def test_creates_the_state_directory_and_lock_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            with operation_lock(state):
                self.assertTrue((state / LOCK_FILE_NAME).exists())

    def test_lock_can_be_taken_again_after_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            with operation_lock(state):
                pass
            with operation_lock(state):
                pass


if __name__ == "__main__":
    unittest.main()
