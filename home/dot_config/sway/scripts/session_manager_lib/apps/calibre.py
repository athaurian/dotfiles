"""Calibre ebook viewer: document resolution, state inspection, and restore."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import subprocess
from pathlib import Path

from ..config import APP_PROFILES, CALIBRE_CONFIG, CALIBRE_DB
from ..ipc import WindowEventWatcher, matching_window_ids
from ._common import reap_if_needed

log = logging.getLogger("session_manager")


def calibre_title_from_window(name: str) -> tuple[str, str] | None:
    match = re.search(r"^(?P<title>.+?) \[(?P<format>[^\]]+)\] — E-book viewer$", name)
    if match:
        return match.group("title").strip(), match.group("format").upper()
    if name == "E-book viewer":
        return "", "EMPTY"
    return None


def _resolve_calibre_document_from_history(title: str, fmt: str) -> str | None:
    if not CALIBRE_CONFIG.exists():
        return None
    try:
        data = json.loads(CALIBRE_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    recent = data.get("session_data", {}).get("standalone_recently_opened", [])
    if not isinstance(recent, list) or not recent:
        return None

    candidates = []
    for entry in recent:
        if not isinstance(entry, dict):
            continue
        json_path = entry.get("pathtoebook", "")
        if not json_path or not Path(json_path).is_file():
            continue
        json_title = entry.get("title", "")
        ext = Path(json_path).suffix.lstrip(".").upper()
        if fmt == "EMPTY":
            continue
        if title == json_title and (fmt == ext or (fmt == "EPUB" and ext == "KEPUB")):
            candidates.append(str(Path(json_path).resolve()))

    unique = sorted(set(candidates))
    return unique[0] if len(unique) == 1 else None


def _resolve_calibre_document_from_library(title: str, fmt: str) -> str | None:
    if not CALIBRE_DB.is_file():
        return None
    try:
        conn = sqlite3.connect(str(CALIBRE_DB), timeout=5)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        return None

    try:
        rows = conn.execute(
            "SELECT books.path, data.format, data.name FROM books "
            "LEFT JOIN data ON data.book = books.id WHERE books.title = ? "
            "ORDER BY books.id, data.format",
            (title,),
        ).fetchall()

        candidates = []
        for row in rows:
            book_path = row["path"]
            book_fmt = (row["format"] or "").upper()
            name = row["name"] or ""
            if not book_path or not book_fmt or not name:
                continue
            if (
                fmt != "EMPTY"
                and book_fmt != fmt
                and not (fmt == "EPUB" and book_fmt == "KEPUB")
            ):
                continue
            candidate_dir = Path.home() / "Library" / book_path
            for variant_name in (name, name.replace(" ", "_")):
                candidate = candidate_dir / variant_name
                if candidate.is_file():
                    candidates.append(str(candidate.resolve()))
                    break

        unique = sorted({p for p in candidates if Path(p).is_file()})
        if len(unique) == 1:
            return unique[0]
    except sqlite3.Error:
        pass
    finally:
        conn.close()
    return None


def get_ebook_viewer_document(title: str, fmt: str) -> str | None:
    if fmt == "EMPTY":
        return ""
    doc_path = _resolve_calibre_document_from_history(title, fmt)
    if doc_path is not None:
        return doc_path
    return _resolve_calibre_document_from_library(title, fmt)


def launch_ebook_viewer(node: dict, claimed_ids: set[int]) -> int | None:
    from .generic import wait_for_app_window

    document_path = node.get("document_path", "")
    app_id = "calibre-ebook-viewer"
    class_name = node.get("class", "")

    if document_path and Path(document_path).is_file():
        cmd = ["ebook-viewer", document_path]
    else:
        cmd = ["ebook-viewer"]

    profile = APP_PROFILES[app_id]
    baseline_ids = set(matching_window_ids(app_id, class_name))

    proc = None
    with WindowEventWatcher() as watcher:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            win_id = wait_for_app_window(
                app_id,
                class_name,
                watcher,
                settle=profile["settle"],
                reject_floating=profile["reject_floating"],
                timeout=profile["timeout"],
                baseline_ids=baseline_ids,
                claimed_ids=claimed_ids,
                process=proc,
                fail_fast_on_exit=True,
            )
        finally:
            reap_if_needed(proc)

    if win_id:
        claimed_ids.add(win_id)
    return win_id
