"""Stale swapfile detection and cleanup."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..config import STATE_DIR, escape_cwd

log = logging.getLogger("session_manager")


_PATH_COMMANDS = ("badd", "edit", "buffer", "cd", "lcd")


def _parse_vim_token(text: str) -> str:
    """Consume one whitespace-terminated Vim token, honouring backslash escapes."""
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(text[i + 1])
            i += 2
            continue
        if ch.isspace():
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _extract_path_from_line(line: str) -> str | None:
    stripped = line.lstrip()
    for cmd in _PATH_COMMANDS:
        prefix = cmd + " "
        if not stripped.startswith(prefix):
            continue
        rest = stripped[len(prefix) :].lstrip()
        # Handle `badd +LNUM path` by dropping the +LNUM token.
        if cmd == "badd" and rest.startswith("+"):
            m = re.match(r"\+\d+\s+", rest)
            if m:
                rest = rest[m.end() :]
        token = _parse_vim_token(rest)
        return token or None
    return None


def cleanup_stale_swapfiles(snapshot_path: Path) -> int:
    removed = 0
    try:
        text = snapshot_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    swap_dir = STATE_DIR / "nvim" / "swap"

    file_refs: set[str] = set()
    for line in text.splitlines():
        path = _extract_path_from_line(line)
        if not path:
            continue
        file_refs.add(str(Path(path).expanduser().resolve()))

    for f_str in file_refs:
        f = Path(f_str)
        if f.exists():
            continue
        swap_name = escape_cwd(str(f)) + ".swp"
        swap_path = swap_dir / swap_name
        if not swap_path.exists():
            continue
        log.info(
            "Removing stale swapfile %s (original file %s is gone)",
            swap_path,
            f,
        )
        try:
            swap_path.unlink()
            removed += 1
        except OSError as exc:
            log.warning("Could not remove swapfile %s: %s", swap_path, exc)

    return removed
