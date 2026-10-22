"""Renders fzf previews as full entry text or kitty image placeholders.

Images are sent through ``kitten icat --unicode-placeholder``. The Unicode
placeholder protocol keeps the image in the terminal grid, so fzf's next
redraw overwrites it like ordinary text. Pixel graphics (sixel and friends)
are deliberately avoided: fzf redraws its preview pane with cell writes,
which cannot erase already-painted pixels, so an oversized sixel image would
linger on screen after the highlight moves on.

Text decoding accepts UTF-8 as well as UTF-16 without a BOM: browsers may
place copied content (for example image URLs from search results) on the
clipboard UTF-16LE encoded, which would otherwise show up as an opaque binary
blob.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

# Preview pane budget in terminal cells, capped against stray environment
# values.
MAX_PREVIEW_WIDTH = 100
MAX_PREVIEW_HEIGHT = 50


def _magick() -> str | None:
    return shutil.which("magick")


def _env_int(name: str, fallback: int) -> int:
    try:
        return int(os.environ.get(name, str(fallback)))
    except ValueError:
        return fallback


def pane_size() -> tuple[int, int]:
    """Gets the preview pane size in cells from fzf, with sane fallbacks."""
    width = _env_int("FZF_PREVIEW_COLUMNS", 80)
    height = _env_int("FZF_PREVIEW_LINES", 24)
    return (
        max(10, min(width, MAX_PREVIEW_WIDTH)),
        max(4, min(height, MAX_PREVIEW_HEIGHT)),
    )


def is_image(data: bytes) -> bool:
    """Checks whether ``data`` is an image ImageMagick can identify."""
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
    text. Anything else must clear a strongly-ASCII bar, because CJK
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
        # Only BOM-marked text is unambiguous. Parity-indicated text must
        # also read as mostly ASCII, since CJK and stray binary decode to
        # printable characters too.
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


def _trim_icat_output(out: bytes) -> bytes:
    """Drops kitty's trailing reset line and appends it to the new last line.

    ``kitten icat`` ends with an ANSI reset without a newline. fzf treats
    that as an extra line and draws a scroll indicator, so the official
    fzf preview helper deletes the last line and reattaches the reset to
    the previous one. Do the same without spawning two ``sed`` processes.
    """
    lines = out.splitlines(keepends=True)
    if lines:
        lines.pop()
    if not lines:
        return b""
    lines[-1] = lines[-1].rstrip(b"\r\n") + b"\x1b[m\n"
    return b"".join(lines)


def render_image(data: bytes) -> bytes | None:
    """Renders image bytes with kitty's Unicode placeholder protocol.

    Returns the escape sequence stream, or ``None`` when kitty's ``kitten``
    is unavailable or rendering fails.
    """
    kitten = shutil.which("kitten")
    if kitten is None:
        return None
    width, height = pane_size()
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(data)
        tmp.flush()
        result = subprocess.run(
            [
                kitten,
                "icat",
                "--clear",
                "--transfer-mode=memory",
                "--unicode-placeholder",
                "--stdin=no",
                f"--place={width}x{height}@0x0",
                tmp.name,
            ],
            check=False,
            capture_output=True,
        )
    if result.returncode != 0 or not result.stdout:
        return None
    return _trim_icat_output(result.stdout) or None


def render(data: bytes) -> None:
    """Writes ``data`` to stdout as an image or text."""
    out = sys.stdout.buffer
    if is_image(data):
        rendered = render_image(data)
        if rendered is not None:
            out.write(rendered)
        else:
            out.write(f"[image: {len(data)} bytes]\n".encode())
        out.flush()
        return
    text = decode_text(data)
    if text is None:
        text = f"[{len(data)} bytes of binary data]\n"
    out.write(text.encode("utf-8"))
    out.flush()
