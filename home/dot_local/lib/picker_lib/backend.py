"""Selects the clipboard-history backend for the current session.

The picker UI is backend-agnostic. A backend supplies the history
entries, decodes a selected entry, and copies bytes back to the
clipboard. ``cliphist`` is the Wayland implementation; an X11 backend can
be registered here later without touching the picker.
"""

from __future__ import annotations

import os
from typing import Protocol


class EntryNotFoundError(RuntimeError):
    """Raised when an entry vanishes between listing and decoding."""


class Backend(Protocol):
    """The operations the picker needs from a clipboard-history store."""

    name: str

    def available(self) -> bool: ...
    def list_entries(self, db_path: str | None = None) -> list[tuple[int, str]]: ...
    def decode(self, payload: bytes, db_path: str | None = None) -> bytes: ...
    def copy_to_clipboard(self, data: bytes) -> None: ...


def get_backend(name: str | None = None) -> Backend | None:
    """Returns the named backend, or the one matching this session.

    ``CLIPBOARD_BACKEND`` overrides autodetection. Returns ``None`` when
    the session has no supported backend, so the picker can report that
    instead of trying a store that cannot work there.
    """
    selected = name or os.environ.get("CLIPBOARD_BACKEND") or _detect()
    if selected == "cliphist":
        from picker_lib.cliphist import CliphistBackend

        return CliphistBackend()
    return None


def _detect() -> str | None:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "cliphist"
    return None
