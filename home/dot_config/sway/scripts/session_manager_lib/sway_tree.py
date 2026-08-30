"""Sway tree serialization (save-side clean_tree)."""

from __future__ import annotations

import logging
from pathlib import Path

from .apps.calibre import calibre_title_from_window, get_ebook_viewer_document
from .apps.mpv import get_mpv_info
from .apps.thunar import get_thunar_info
from .apps.zathura import get_zathura_info
from .config import NVIM_SESSION_DIR, escape_cwd
from .ipc import node_class
from .nvim.inspect import get_foot_nvim_state, is_dashboard_state
from .nvim.snapshot import (
    create_manager_snapshot,
    get_nvim_snapshot_path,
    snacks_sidecar_path,
)
from .nvim.sockets import nvim_socket_path
from .proc_cache import ProcCache

log = logging.getLogger("session_manager")


def _legacy_session_file(cwd: str) -> str:
    sf = NVIM_SESSION_DIR / f"{escape_cwd(cwd)}.vim"
    return str(sf) if sf.exists() else ""


def clean_tree(node: dict, cache: ProcCache) -> dict | None:
    ntype = node.get("type")
    cls = node_class(node)

    if ntype in ("con", "floating_con") and (node.get("app_id") or cls):
        raw_app_id = node.get("app_id", "")
        app_id = "foot" if raw_app_id.startswith("foot_restored_") else raw_app_id
        pid = node.get("pid", 0)
        info: dict[str, object] = {}

        if app_id in ("foot", "foot_drop"):
            cwd = cache.get_foot_cwd(pid) if pid else str(Path.home())
            zellij_sess = cache.get_zellij_session(pid) if pid else None
            is_ssh, ssh_cmd = cache.is_ssh_or_sudo(pid) if pid else (False, "")
            nvim_pid = cache.get_nvim_pid(pid) if pid else None

            if zellij_sess is not None:
                info["nvim_type"] = "none"
                info["zellij_session"] = zellij_sess
                info["cwd"] = cwd
                log.info("Foot %s has zellij session %s", pid, zellij_sess)
            elif is_ssh:
                info["nvim_type"] = "none"
                info["was_ssh"] = ssh_cmd
                info["cwd"] = cwd
                log.info("Foot %s is ssh/sudo (%s), saving cwd only", pid, ssh_cmd)
            elif nvim_pid is not None:
                nvim_server_pid, live_state = get_foot_nvim_state(pid, cache)

                if live_state is None:
                    info["nvim_type"] = "unknown"
                    info["session_file"] = _legacy_session_file(cwd)
                elif is_dashboard_state(live_state):
                    info["nvim_type"] = "dashboard"
                else:
                    snapshot_path = get_nvim_snapshot_path(cwd, nvim_server_pid)
                    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
                    server_path = (
                        str(nvim_socket_path(nvim_server_pid))
                        if nvim_server_pid is not None
                        else ""
                    )
                    ok, err = create_manager_snapshot(
                        server_path, snapshot_path, nvim_server_pid
                    )
                    if ok and snapshot_path.exists():
                        info["nvim_type"] = "session"
                        info["nvim_snapshot"] = str(snapshot_path)
                        sidecar = snacks_sidecar_path(snapshot_path)
                        if sidecar.exists():
                            info["nvim_snacks_sidecar"] = str(sidecar)
                    else:
                        info["nvim_type"] = "unknown"
                        info["session_file"] = _legacy_session_file(cwd)
                        log.warning(
                            "Failed to snapshot nvim in %s (using file): %s", cwd, err
                        )
                info["cwd"] = cwd
            else:
                info["nvim_type"] = "none"
                info["cwd"] = cwd

        elif app_id == "org.pwmt.zathura":
            doc, page = get_zathura_info(pid)
            info = {"document_path": doc, "page_number": page}

        elif app_id == "calibre-ebook-viewer":
            parsed = calibre_title_from_window(node.get("name", ""))
            if parsed is not None:
                title_part, fmt = parsed
                doc_path = get_ebook_viewer_document(title_part, fmt)
                info = {
                    "document_path": doc_path or "",
                    "calibre_format": fmt,
                }
            else:
                info = {"document_path": "", "calibre_format": ""}

        elif app_id == "thunar":
            folder = get_thunar_info(pid)
            info = {"folder_path": folder}

        elif app_id == "mpv":
            media = get_mpv_info(pid)
            info = {"media_path": media}

        percent = node.get("percent")
        window: dict[str, object] = {
            "type": "window",
            "app_id": app_id,
            "class": cls,
            "name": node.get("name", ""),
            "pid": pid,
            "fullscreen_mode": node.get("fullscreen_mode", 0),
            "rect": node.get("rect", {}),
            "marks": node.get("marks", []),
            "scratchpad_state": node.get("scratchpad_state", "none"),
            **info,
        }
        if isinstance(percent, (int, float)):
            window["percent"] = float(percent)
        return window

    if ntype in ("con", "workspace"):
        children = [c for n in node.get("nodes", []) if (c := clean_tree(n, cache))]
        floating = [
            c for n in node.get("floating_nodes", []) if (c := clean_tree(n, cache))
        ]
        if ntype == "con" and not children and not floating:
            return None
        result: dict[str, object] = {
            "type": ntype,
            "layout": node.get("layout"),
            "nodes": children,
            "floating_nodes": floating,
        }
        percent = node.get("percent")
        if isinstance(percent, (int, float)):
            result["percent"] = float(percent)
        return result
    return None
