"""Tests for backend selection."""

import os
import unittest
import unittest.mock

from picker_lib import backend


class TestGetBackend(unittest.TestCase):
    def test_wayland_selects_cliphist(self):
        with unittest.mock.patch.dict(
            os.environ, {"WAYLAND_DISPLAY": "wayland-1"}, clear=True
        ):
            selected = backend.get_backend()
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.name, "cliphist")

    def test_no_session_returns_none(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(backend.get_backend())

    def test_explicit_name_wins(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            selected = backend.get_backend("cliphist")
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.name, "cliphist")

    def test_environment_override(self):
        with unittest.mock.patch.dict(
            os.environ, {"CLIPBOARD_BACKEND": "cliphist"}, clear=True
        ):
            selected = backend.get_backend()
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.name, "cliphist")

    def test_unknown_name_returns_none(self):
        self.assertIsNone(backend.get_backend("no-such-backend"))


if __name__ == "__main__":
    unittest.main()
