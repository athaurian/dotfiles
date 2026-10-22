"""Tests for ``picker_lib.preview``: text, UTF-16, images, and binary."""

import io
import shutil
import subprocess
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


def _completed(stdout: bytes = b"", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=b""
    )


class _FakeStdout:
    """Minimal stdout replacement exposing the binary buffer render uses."""

    def __init__(self):
        self.buffer = io.BytesIO()


class TestDecodeText(unittest.TestCase):
    def test_utf8(self):
        self.assertEqual(preview.decode_text(b"hello"), "hello")

    def test_utf16le_without_bom(self):
        self.assertEqual(preview.decode_text(UTF16_URL), "https://example.com/img.png")

    def test_utf16be_without_bom(self):
        data = "https://example.com/img.png".encode("utf-16-be")
        self.assertEqual(preview.decode_text(data), "https://example.com/img.png")

    def test_utf16_with_bom(self):
        data = "hello".encode("utf-16")
        self.assertEqual(preview.decode_text(data), "hello")

    def test_binary_returns_none(self):
        self.assertIsNone(preview.decode_text(b"\x00\x01\x02\x03"))

    def test_escape_sequences_are_not_text(self):
        # Clipboard text must never be able to inject terminal escapes.
        self.assertIsNone(preview.decode_text(b"\x1b[2Jwiped"))

    def test_empty_returns_none(self):
        self.assertIsNone(preview.decode_text(b""))


class TestPaneSize(unittest.TestCase):
    def test_reads_fzf_environment(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "40", "FZF_PREVIEW_LINES": "10"},
        ):
            self.assertEqual(preview.pane_size(), (40, 10))

    def test_caps_oversized_panes(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "200", "FZF_PREVIEW_LINES": "100"},
        ):
            self.assertEqual(
                preview.pane_size(),
                (preview.MAX_PREVIEW_WIDTH, preview.MAX_PREVIEW_HEIGHT),
            )

    def test_enforces_minimums(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "1", "FZF_PREVIEW_LINES": "1"},
        ):
            self.assertEqual(preview.pane_size(), (10, 4))

    def test_falls_back_on_garbage(self):
        with unittest.mock.patch.dict(
            preview.os.environ,
            {"FZF_PREVIEW_COLUMNS": "wide", "FZF_PREVIEW_LINES": "tall"},
        ):
            self.assertEqual(preview.pane_size(), (80, 24))


@unittest.skipIf(NEEDS_MAGICK, "magick not installed")
class TestIsImage(unittest.TestCase):
    def test_png_is_image(self):
        self.assertTrue(preview.is_image(PIXEL_PNG))

    def test_text_is_not_image(self):
        self.assertFalse(preview.is_image(b"just a note"))


class TestTrimIcatOutput(unittest.TestCase):
    def test_drops_final_reset_line(self):
        self.assertEqual(
            preview._trim_icat_output(b"placeholder\n\x1b[m"),
            b"placeholder\x1b[m\n",
        )

    def test_handles_reset_with_newline(self):
        self.assertEqual(
            preview._trim_icat_output(b"placeholder\n\x1b[m\n"),
            b"placeholder\x1b[m\n",
        )

    def test_empty_stays_empty(self):
        self.assertEqual(preview._trim_icat_output(b""), b"")


class TestRenderImage(unittest.TestCase):
    def test_missing_kitten_returns_none(self):
        with unittest.mock.patch.object(preview.shutil, "which", return_value=None):
            self.assertIsNone(preview.render_image(PIXEL_PNG))

    def test_kitten_command_and_output(self):
        with (
            unittest.mock.patch.dict(
                preview.os.environ,
                {"FZF_PREVIEW_COLUMNS": "40", "FZF_PREVIEW_LINES": "10"},
            ),
            unittest.mock.patch.object(
                preview.shutil, "which", return_value="/usr/bin/kitten"
            ),
            unittest.mock.patch.object(
                preview.subprocess,
                "run",
                return_value=_completed(b"placeholder\n\x1b[m"),
            ) as run,
        ):
            rendered = preview.render_image(PIXEL_PNG)
        self.assertEqual(rendered, b"placeholder\x1b[m\n")
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "/usr/bin/kitten")
        self.assertIn("icat", argv)
        self.assertIn("--clear", argv)
        self.assertIn("--transfer-mode=memory", argv)
        self.assertIn("--unicode-placeholder", argv)
        self.assertIn("--stdin=no", argv)
        self.assertIn("--place=40x10@0x0", argv)
        self.assertTrue(argv[-1].endswith(".png") or argv[-1].isprintable())

    def test_failed_icat_returns_none(self):
        with (
            unittest.mock.patch.object(
                preview.shutil, "which", return_value="/usr/bin/kitten"
            ),
            unittest.mock.patch.object(
                preview.subprocess, "run", return_value=_completed(returncode=1)
            ),
        ):
            self.assertIsNone(preview.render_image(PIXEL_PNG))

    def test_empty_output_returns_none(self):
        with (
            unittest.mock.patch.object(
                preview.shutil, "which", return_value="/usr/bin/kitten"
            ),
            unittest.mock.patch.object(
                preview.subprocess, "run", return_value=_completed(b"")
            ),
        ):
            self.assertIsNone(preview.render_image(PIXEL_PNG))


class TestRender(unittest.TestCase):
    def _render(self, data: bytes) -> bytes:
        fake = _FakeStdout()
        with unittest.mock.patch.object(preview.sys, "stdout", fake):
            preview.render(data)
        return fake.buffer.getvalue()

    def test_renders_text(self):
        with unittest.mock.patch.object(preview, "is_image", return_value=False):
            self.assertEqual(self._render(b"hello"), b"hello")

    def test_binary_placeholder(self):
        with unittest.mock.patch.object(preview, "is_image", return_value=False):
            self.assertEqual(
                self._render(b"\x00\x01\x02\x03"),
                b"[4 bytes of binary data]\n",
            )

    def test_escape_sequences_never_reach_terminal(self):
        with unittest.mock.patch.object(preview, "is_image", return_value=False):
            out = self._render(b"\x1b[2Jwiped")
        self.assertNotIn(b"\x1b", out)
        self.assertIn(b"binary data", out)

    def test_renders_image(self):
        with (
            unittest.mock.patch.object(preview, "is_image", return_value=True),
            unittest.mock.patch.object(preview, "render_image", return_value=b"IMAGE"),
        ):
            self.assertEqual(self._render(b"whatever"), b"IMAGE")

    def test_image_fallback_reports_size(self):
        with (
            unittest.mock.patch.object(preview, "is_image", return_value=True),
            unittest.mock.patch.object(preview, "render_image", return_value=None),
        ):
            self.assertEqual(self._render(b"whatever"), b"[image: 8 bytes]\n")


if __name__ == "__main__":
    unittest.main()
