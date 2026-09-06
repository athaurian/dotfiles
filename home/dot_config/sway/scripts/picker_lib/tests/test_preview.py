"""Tests for ``picker_lib.preview`` covering text, UTF-16, images, and binary."""

import io
import shutil
import unittest
import unittest.mock

from picker_lib import preview

# Minimal 1x1 transparent PNG.
PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Browsers may store copied URLs UTF-16LE encoded, as seen with image
# URLs copied from search results, for example b"h\\x00t\\x00t\\x00p...".
UTF16_URL = "https://example.com/img.png".encode("utf-16-le")

NEEDS_MAGICK = shutil.which("magick") is None


def _solid_png(width, height, color):
    """Builds solid-color PNG bytes with ``magick`` for test fixtures."""
    import subprocess
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "solid.png")
        subprocess.run(
            ["magick", "-size", f"{width}x{height}", f"xc:{color}", path],
            check=True,
            capture_output=True,
        )
        return Path(path).read_bytes()


class TestDecodeText(unittest.TestCase):
    def test_utf8_passes_through(self):
        self.assertEqual(preview.decode_text(b"hello: world"), "hello: world")

    def test_utf8_multiline_passes_through(self):
        self.assertEqual(preview.decode_text(b"a\nb"), "a\nb")

    def test_utf16le_decodes(self):
        self.assertEqual(preview.decode_text(UTF16_URL), "https://example.com/img.png")

    def test_utf16be_decodes(self):
        data = "https://example.com/img.png".encode("utf-16-be")
        self.assertEqual(preview.decode_text(data), "https://example.com/img.png")

    def test_utf16_with_bom_decodes(self):
        data = "https://example.com/img.png".encode("utf-16")
        self.assertEqual(preview.decode_text(data), "https://example.com/img.png")

    def test_cjk_utf8_passes_through(self):
        data = "日本語テスト".encode()
        self.assertEqual(preview.decode_text(data), "日本語テスト")

    def test_nul_laced_binary_returns_none(self):
        self.assertIsNone(preview.decode_text(b"\x00\xff\x00\xfe\x01\x02"))

    def test_hostile_text_returned_literally(self):
        data = b'x $(touch /tmp/picker-pwned) y `id` "q"'
        self.assertEqual(preview.decode_text(data), data.decode())

    def test_binary_returns_none(self):
        self.assertIsNone(preview.decode_text(b"\x00\x01\x02binary"))

    def test_empty_returns_none(self):
        self.assertIsNone(preview.decode_text(b""))


class TestRender(unittest.TestCase):
    def _render(self, data):
        buffer = io.BytesIO()
        stdout = unittest.mock.Mock()
        stdout.buffer = buffer
        with unittest.mock.patch.object(preview.sys, "stdout", stdout):
            preview.render(data)
        return buffer.getvalue()

    def test_text_passes_through(self):
        self.assertEqual(self._render(b"hello: world\nline2"), b"hello: world\nline2")

    def test_utf16_url_renders_readable(self):
        self.assertEqual(self._render(UTF16_URL), b"https://example.com/img.png")

    def test_binary_falls_back_to_placeholder(self):
        out = self._render(b"\x00\x01\x02binary")
        self.assertIn(b"bytes of binary data", out)

    def test_escape_sequences_never_reach_terminal(self):
        out = self._render(b"\x1b[2Jwiped")
        self.assertNotIn(b"\x1b[2J", out)


@unittest.skipIf(NEEDS_MAGICK, "magick not installed")
class TestRenderImage(unittest.TestCase):
    def test_is_image(self):
        self.assertTrue(preview.is_image(PIXEL_PNG))
        self.assertFalse(preview.is_image(b"just text"))
        self.assertFalse(preview.is_image(b""))

    def test_renders_grid_cells_not_pixel_graphics(self):
        art = preview.render_image(PIXEL_PNG)
        assert art is not None
        # Half blocks with 24-bit color and no sixel device-control strings.
        self.assertIn("▀", art)
        self.assertIn("\x1b[38;2;", art)
        # ``fzf`` redraws cannot erase sixel output from the preview pane.
        self.assertNotIn("\x1bP", art)

    def test_solid_red_cells(self):
        red = _solid_png(2, 2, "red")
        art = preview.render_image(red)
        assert art is not None
        rows = art.splitlines()
        self.assertEqual(len(rows), 1)  # two image rows per text row
        self.assertIn("\x1b[38;2;255;0;0m", rows[0])
        self.assertIn("\x1b[48;2;255;0;0m", rows[0])

    def test_odd_row_keeps_terminal_background(self):
        blue = _solid_png(1, 1, "blue")
        art = preview.render_image(blue)
        assert art is not None
        # Unpaired last row uses foreground color only, with no invented background.
        self.assertIn("\x1b[38;2;0;0;255m▀\x1b[0m", art)
        self.assertNotIn("48;2;", art)

    def test_render_via_entry(self):
        buffer = io.BytesIO()
        stdout = unittest.mock.Mock()
        stdout.buffer = buffer
        with unittest.mock.patch.object(preview.sys, "stdout", stdout):
            preview.render(PIXEL_PNG)
        out = buffer.getvalue()
        self.assertIn("▀".encode(), out)
        self.assertNotIn(b"\x1bP", out)


class TestPaneSize(unittest.TestCase):
    def test_fzf_env_honored_and_capped(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "40", "FZF_PREVIEW_LINES": "10"},
        ):
            self.assertEqual(preview.pane_size(), (40, 10))

    def test_fallbacks_and_caps(self):
        with unittest.mock.patch.dict(preview.os.environ, {}, clear=False):
            width, height = preview.pane_size()
            self.assertLessEqual(width, preview.MAX_PREVIEW_WIDTH)
            self.assertLessEqual(height, preview.MAX_PREVIEW_HEIGHT)

    def test_garbage_env_falls_back(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "wide", "FZF_PREVIEW_LINES": "tall"},
        ):
            self.assertEqual(preview.pane_size(), (80, 24))


if __name__ == "__main__":
    unittest.main()
