"""Session save orchestration."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from pathlib import Path

from .background import detect_background_apps
from .config import (
    BACKGROUND_APPS_FILE,
    NVIM_SESSION_DIR,
    SCRATCHPAD_WORKSPACE,
    STATE_DIR,
    STATE_FILE,
)
from .ipc import close_connection, get_tree, walk_tree
from .locking import operation_lock
from .logging_setup import notify
from .proc_cache import ProcCache
from .sway_tree import clean_tree

log = logging.getLogger("session_manager")


def _focused_workspace_name(tree: dict) -> str | None:
    """Name of the focused non-scratchpad workspace, if any."""

    def _walk(node: dict, ws_name: str | None) -> str | None:
        if node.get("type") == "workspace":
            ws_name = node.get("name")
        if node.get("focused"):
            return ws_name if ws_name and ws_name != SCRATCHPAD_WORKSPACE else None
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            found = _walk(child, ws_name)
            if found:
                return found
        return None

    for output in tree.get("nodes", []):
        found = _walk(output, None)
        if found:
            return found
    return None


def _atomic_write(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.tmp",
        delete=False,
    ) as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
        tmp_path = f.name
    os.replace(tmp_path, path)


def save_session(*, notify_user: bool = True) -> None:
    backup_msg = ""
    try:
        with operation_lock(STATE_DIR):
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            NVIM_SESSION_DIR.mkdir(parents=True, exist_ok=True)
            (STATE_DIR / "nvim" / "manager").mkdir(parents=True, exist_ok=True)

            tree = get_tree()
            cache = ProcCache.snapshot()

            workspaces = []
            hidden_scratchpad = []

            for output in tree.get("nodes", []):
                for ws in output.get("nodes", []):
                    if ws.get("type") != "workspace":
                        continue
                    if ws.get("name") == SCRATCHPAD_WORKSPACE:
                        for child in ws.get("floating_nodes", []):
                            cleaned = clean_tree(child, cache)
                            if cleaned:
                                hidden_scratchpad.append(cleaned)
                        continue
                    cleaned = clean_tree(ws, cache)
                    if cleaned and (
                        cleaned.get("nodes") or cleaned.get("floating_nodes")
                    ):
                        cleaned["name"] = ws.get("name")
                        workspaces.append(cleaned)

            background_apps = detect_background_apps(cache, tree=tree)

            # If helium windows are present, give it a moment to flush its
            # Session/Tabs files so --restore-last-session will see both windows.
            has_helium = any(
                n.get("app_id") == "helium" for ws in workspaces for n in walk_tree(ws)
            )
            if has_helium:
                time.sleep(0.8)

            payload = {
                "version": 2,
                "workspaces": workspaces,
                "hidden_scratchpad": hidden_scratchpad,
                "background_apps": background_apps,
                "focused_workspace": _focused_workspace_name(tree),
            }

            # Rotate backups before overwriting: STATE_FILE.3 <- .2 <- .1 <- STATE_FILE
            backup_msg = ""
            if STATE_FILE.exists():
                try:
                    for i in range(3, 0, -1):
                        src = (
                            STATE_FILE
                            if i == 1
                            else STATE_FILE.with_name(f"{STATE_FILE.name}.{i - 1}")
                        )
                        dst = STATE_FILE.with_name(f"{STATE_FILE.name}.{i}")
                        if src.exists():
                            # Remove oldest beyond 3 first via overwrite
                            try:
                                if dst.exists():
                                    dst.unlink()
                            except OSError:
                                pass
                            src.replace(dst)
                    backup_msg = " (backup .1 created)"
                    log.info(
                        "Rotated backups: %s -> %s.1/.2/.3", STATE_FILE, STATE_FILE
                    )
                except OSError as exc:
                    log.warning("Backup rotation failed for %s: %s", STATE_FILE, exc)

            # Authoritative single commit. Restore reads background_apps from
            # this file when present, preventing mixed-generation restore.
            _atomic_write(STATE_FILE, json.dumps(payload, indent=2))

            # Compatibility sidecar for older versions/tools. It is no longer
            # authoritative and must not make the main save fail.
            try:
                _atomic_write(
                    BACKGROUND_APPS_FILE, json.dumps(background_apps, indent=2)
                )
                log.info("Background apps saved to %s", BACKGROUND_APPS_FILE)
            except OSError as exc:
                log.warning(
                    "Could not write compatibility background apps file %s: %s",
                    BACKGROUND_APPS_FILE,
                    exc,
                )

            log.info("Session saved to %s%s", STATE_FILE, backup_msg)
    finally:
        close_connection()

    if notify_user:
        notify(f"session saved successfully{backup_msg}")
