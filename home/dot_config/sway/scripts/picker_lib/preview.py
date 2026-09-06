"""Renders fzf previews as full entry text or terminal cell art for images.

Images render as 24-bit half-block art (two image rows per text row),
which lives in the terminal grid like any other text. Pixel graphics
(sixel and friends) are deliberately avoided: fzf redraws its preview
pane with cell writes, which cannot erase already-painted pixels, so an
oversized sixel image would linger on screen after the highlight moves
on. Cell art is overwritten by the next redraw by construction.

Text decoding accepts UTF-8 as well as UTF-16 without a BOM: browsers
may place copied content (for example image URLs from search results)
on the clipboard UTF-16LE encoded, which would otherwise show up as an
opaque binary blob.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

# Preview pane budget in terminal cells. Height counts text rows while
# each row carries two image rows via half blocks.
MAX_PREVIEW_WIDTH = 100
MAX_PREVIEW_HEIGHT = 50

_PIXEL_RE = re.compile(r"^(\d+),(\d+): \(([^)]+)\)")


def _magick() -> str | None:
    return shutil.which("magick")


def pane_size() -> tuple[int, int]:
    """The preview pane size in cells from fzf, with sane fallbacks."""
    try:
        width = int(os.environ.get("FZF_PREVIEW_COLUMNS", "80"))
    except ValueError:
        width = 80
    try:
        height = int(os.environ.get("FZF_PREVIEW_LINES", "24"))
    except ValueError:
        height = 24
    return (
        max(10, min(width, MAX_PREVIEW_WIDTH)),
        max(4, min(height, MAX_PREVIEW_HEIGHT)),
    )


def is_image(data: bytes) -> bool:
    """Checks whether ``data`` is an image ImageMagick can render."""
    magick = _magick()
    if magick is None or not data:
        return False
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(data)
        tmp.flush()
        result = subprocess.run(
            [magick, "identify", tmp.name],
            check=False,
            capture_output=True,
        )
    return result.returncode == 0


def decode_text(data: bytes) -> str | None:
    """Decodes clipboard bytes to displayable text, or ``None`` if binary.

    Accepts UTF-8 and BOM-less UTF-16 (browsers may place copied content,
    for example image URLs from search results, on the clipboard UTF-16
    encoded). Endianness comes from the NUL-byte parity of ASCII-range
    text; anything else must clear a strongly-ASCII bar, because CJK
    text decodes to printable characters either way.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        if text and _printable(text):
            return text
    candidates: list[str] = []
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        candidates.append("utf-16")
    elif b"\x00" in data:
        even = sum(1 for i in range(0, len(data), 2) if data[i] == 0)
        odd = sum(1 for i in range(1, len(data), 2) if data[i] == 0)
        if even >= odd:
            candidates.extend(["utf-16-be", "utf-16-le"])
        else:
            candidates.extend(["utf-16-le", "utf-16-be"])
    else:
        return None
    for index, encoding in enumerate(candidates):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        stripped = text.strip("\ufeff \t\n\r")
        # Only BOM-marked text is unambiguous; parity-indicated text must
        # also read as mostly ASCII, since CJK decodes printable either
        # way and stray binary can too.
        if _looks_textual(stripped, ascii_bar=index > 0 or encoding != "utf-16"):
            return stripped
    return None


def _looks_textual(text: str, ascii_bar: bool) -> bool:
    if not text or not _printable(text):
        return False
    if not ascii_bar:
        return True
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / len(text) > 0.5


def _printable(text: str) -> bool:
    return all(c in "\t\n\r" or c.isprintable() for c in text)


def _parse_pixels(txt: str) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Parses ``magick txt:`` output into width, height, and row-major RGB."""
    width = height = 0
    header, _, body = txt.partition("\n")
    match = re.search(r"(\d+),(\d+),", header)
    if match:
        width, height = int(match.group(1)), int(match.group(2))
    pixels: dict[tuple[int, int], tuple[int, int, int]] = {}
    for line in body.splitlines():
        match = _PIXEL_RE.match(line)
        if not match:
            continue
        channels = [c.strip() for c in match.group(3).split(",")]
        try:
            if len(channels) == 1:
                rgb = (int(channels[0]),) * 3
            else:
                rgb = (int(channels[0]), int(channels[1]), int(channels[2]))
        except ValueError:
            continue
        pixels[(int(match.group(1)), int(match.group(2)))] = rgb
    rows = [pixels.get((x, y), (0, 0, 0)) for y in range(height) for x in range(width)]
    return width, height, rows


def render_image(data: bytes) -> str | None:
    """Render image bytes as half-block art, or None when impossible."""
    magick = _magick()
    if magick is None:
        return None
    width, _ = pane_size()
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(data)
        tmp.flush()
        # Two image rows per text row; shrink-only so small art stays crisp.
        converted = subprocess.run(
            [
                magick,
                tmp.name,
                "-thumbnail",
                f"{width}x{MAX_PREVIEW_HEIGHT * 2}>",
                "-depth",
                "8",
                "txt:-",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    if converted.returncode != 0 or not converted.stdout:
        return None
    width, height, rows = _parse_pixels(converted.stdout)
    if width <= 0 or height <= 0:
        return None
    out = []
    for y in range(0, height, 2):
        cells = []
        for x in range(width):
            top = rows[y * width + x]
            if y + 1 >= height:
                # Unpaired last row: the lower half-cell keeps the
                # terminal background instead of inventing a color.
                cells.append(f"\x1b[38;2;{top[0]};{top[1]};{top[2]}m▀\x1b[0m")
            else:
                bottom = rows[(y + 1) * width + x]
                cells.append(
                    f"\x1b[38;2;{top[0]};{top[1]};{top[2]}m"
                    f"\x1b[48;2;{bottom[0]};{bottom[1]};{bottom[2]}m▀"
                )
        out.append("".join(cells) + "\x1b[0m")
    return "\n".join(out) + "\n"


def render(data: bytes) -> None:
    """Write *data* to stdout as cell art (images) or text."""
    out = sys.stdout.buffer
    if is_image(data):
        art = render_image(data)
        if art is not None:
            out.write(art.encode("utf-8"))
            out.flush()
            return
    text = decode_text(data)
    if text is None:
        text = f"[{len(data)} bytes of binary data]\n"
    out.write(text.encode("utf-8"))
    out.flush()
