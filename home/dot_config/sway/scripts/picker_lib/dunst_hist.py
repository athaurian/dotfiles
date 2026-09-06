"""Dunst notification history access via dunstctl.

``dunstctl history`` prints ``{"data": [[entry, ...]]}`` where every entry
is a map of ``{"type": ..., "data": value}`` field objects (for example
``"summary": {"type": "s", "data": "..."}``). Plain values are tolerated
too, so unit fixtures stay readable.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from picker_lib import model

SUMMARY_WIDTH = 80
BODY_WIDTH = 80


def have_dunstctl() -> bool:
    """Checks whether the dunstctl binary is available."""
    return shutil.which("dunstctl") is not None


def _run_dunstctl(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["dunstctl", *args], check=False, capture_output=True, text=True
        )
    except (FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _field(entry: dict[str, Any], name: str) -> Any:
    value = entry.get(name)
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


def _normalize(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    try:
        eid = int(_field(entry, "id"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return {
        "id": eid,
        "summary": str(_field(entry, "summary") or ""),
        "body": str(_field(entry, "body") or ""),
        "appname": str(_field(entry, "appname") or ""),
        "urgency": str(_field(entry, "urgency") or ""),
    }


def _items_of(raw_json: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []
    entries = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list):
        return []
    items = []
    for group in entries:
        candidates = group if isinstance(group, list) else [group]
        for entry in candidates:
            normalized = _normalize(entry)
            if normalized is not None:
                items.append(normalized)
    seen = set()
    unique = []
    for item in items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


def fetch() -> tuple[list[dict[str, Any]] | None, str]:
    """Fetches notification history as items and raw JSON.

    Returns None and an empty string when dunstctl is missing or its
    output has no usable entries.
    """
    out = _run_dunstctl(["history"])
    if out is None:
        return None, ""
    items = _items_of(out)
    if not items:
        return None, ""
    return items, out


def menu_lines(items: list[dict[str, Any]]) -> list[str]:
    """Builds menu lines for ``items``. Each line holds the id, summary, and body."""
    lines = []
    for entry in items:
        try:
            eid = int(entry.get("id", 0))
        except (TypeError, ValueError):
            continue
        summary = model.single_line(str(entry.get("summary") or ""))[:SUMMARY_WIDTH]
        body = model.single_line(str(entry.get("body") or ""))[:BODY_WIDTH]
        lines.append(model.format_entry(eid, f"{summary}: {body}"))
    return lines


def lookup(raw_json: str, eid: int) -> tuple[str, str]:
    """Looks up the exact summary and body for ``eid`` in previously fetched JSON.

    Looks the record up by id instead of re-splitting the display text,
    so colons in the summary or body cannot corrupt the result.
    """
    for entry in _items_of(raw_json):
        if entry["id"] != eid:
            continue
        return entry["summary"], entry["body"]
    return "", ""


def restore_latest() -> None:
    """Asks dunst to re-display the most recently dismissed notification."""
    _run_dunstctl(["history-pop"])
