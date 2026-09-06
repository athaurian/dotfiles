"""Menu line model shared by the clipboard and notification pickers.

The picker contract is that every menu line is ``"<id>\\t<display>"`` where ``<id>``
is a zero-padded decimal id of fixed width and ``<display>`` is a
single-line human-readable summary. Zero-padding keeps the display
column aligned under 2-space tab stops, and ``cliphist decode`` accepts
zero-padded ids since it parses them with ``Atoi``, so the full menu line stays
a valid decode key. Space-padded ids are rejected by ``cliphist`` and
must not be used.
"""

from __future__ import annotations

ID_WIDTH = 4


def format_entry(eid: int, display: str) -> str:
    """Formats one menu line as zero-padded id, tab, display text."""
    return f"{eid:0{ID_WIDTH}d}\t{display}"


def split_entry(line: str) -> tuple[int | None, str]:
    """Splits a menu line into an id and display text. The id is None when malformed."""
    eid, tab, display = line.partition("\t")
    if not tab or not eid.isdigit():
        return None, line
    return int(eid), display


def single_line(text: str) -> str:
    """Collapses newlines to spaces for single-line menu display."""
    return " ".join(text.split())
