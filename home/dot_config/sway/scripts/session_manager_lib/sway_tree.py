"""Serialization of a live Sway/i3 tree into the portable session format."""

from __future__ import annotations

import logging
from pathlib import Path

from .apps.calibre import calibre_title_from_window, get_ebook_viewer_document
from .apps.mpv import get_mpv_info
from .apps.thunar import get_thunar_info
from .apps.zathura import get_zathura_info
from .config import (
    DROP_TERMINAL_INSTANCE,
    DROP_TERMINAL_TITLE,
    NVIM_SESSION_DIR,
    TRANSIENT_TERMINAL_TITLES,
    escape_cwd,
)
from .ipc import node_app_id, node_class, node_instance, node_pid
from .nvim.inspect import get_terminal_nvim_state, is_dashboard_state
from .nvim.snapshot import (
    create_manager_snapshot,
    get_nvim_snapshot_path,
    snacks_sidecar_path,
)
from .nvim.sockets import nvim_socket_path
from .proc_cache import ProcCache

log = logging.getLogger("session_manager")

# The drop terminal is identified by any of its WM_CLASS instance, window name,
# or mark, because each window manager surfaces a different subset of them.
_TRANSIENT_KITTY_TITLES = frozenset(TRANSIENT_TERMINAL_TITLES)
_TRANSIENT_KITTY_INSTANCES = frozenset(TRANSIENT_TERMINAL_TITLES)
_DROP_KITTY_MARK = "drop_term"
_DROP_KITTY_TITLE = DROP_TERMINAL_TITLE
_DROP_KITTY_INSTANCE = DROP_TERMINAL_INSTANCE


def _legacy_session_file(cwd: str) -> str:
    """Return a legacy per-directory session file path, or an empty string."""
    sf = NVIM_SESSION_DIR / f"{escape_cwd(cwd)}.vim"
    return str(sf) if sf.exists() else ""


def _has_window_identity(node: dict) -> bool:
    """Report whether a node carries a window identity."""
    return bool(
        node.get("app_id")
        or node.get("window")
        or node_class(node)
        or node_instance(node)
    )


def _merge_floating_wrapper(node: dict) -> dict | None:
    """Unwraps an i3 ``floating_con`` around its single content window.

    i3 reports floating windows as a wrapper container with one child window.
    The wrapper carries the absolute rect, marks, and scratchpad state, while
    the child carries the pid, title, and WM_CLASS. Sway sometimes reports the
    same information on the wrapper itself, so both shapes are accepted.
    """
    if _has_window_identity(node):
        return node
    if node.get("type") != "floating_con":
        return None

    children = [child for child in node.get("nodes", []) if _has_window_identity(child)]
    if len(children) != 1:
        return None

    merged = dict(children[0])
    wrapper_marks = list(node.get("marks") or [])
    child_marks = list(merged.get("marks") or [])
    if wrapper_marks or child_marks:
        merged["marks"] = list(dict.fromkeys(wrapper_marks + child_marks))

    # Scratchpad state and fullscreen live on the wrapper in i3. Do not let
    # the wrapper's neutral zero values clobber real child values.
    for key in ("scratchpad_state", "fullscreen_mode", "percent"):
        value = node.get(key)
        if value not in (None, 0, 0.0, "", [], {}):
            merged[key] = value

    rect = node.get("rect") or {}
    if rect.get("width") and rect.get("height"):
        merged["rect"] = rect
    return merged


def _identity_descendants(node: dict) -> list[dict]:
    """Return the window-bearing descendants of a container."""
    found: list[dict] = []
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        if _has_window_identity(child):
            found.append(child)
        else:
            found.extend(_identity_descendants(child))
    return found


def _window_source(node: dict) -> dict | None:
    """Return the node carrying a window's identity, unwrapping i3 floats."""
    if _has_window_identity(node):
        return node
    return _merge_floating_wrapper(node)


def _kitty_app_id(node: dict, app_id: str) -> str | None:
    """Classify kitty windows and drop transient scratchpad terminals."""
    if app_id != "kitty":
        return app_id

    title = node.get("name") or ""
    instance = node_instance(node)
    marks = node.get("marks") or []

    if (
        title in _TRANSIENT_KITTY_TITLES
        or instance in _TRANSIENT_KITTY_INSTANCES
        or any(mark in _TRANSIENT_KITTY_INSTANCES for mark in marks)
    ):
        return None

    if (
        title == _DROP_KITTY_TITLE
        or instance == _DROP_KITTY_INSTANCE
        or _DROP_KITTY_MARK in marks
    ):
        return "kitty_drop"
    return app_id


def clean_floating(node: dict, cache: ProcCache) -> list[dict]:
    """Clean one floating child into the windows it holds.

    i3 wraps a floating window in a ``floating_con``. A floating group (two
    tabbed windows, say) holds several of them under the wrapper, so each
    window is kept separately instead of dropping the whole group.
    """
    cleaned = clean_tree(node, cache)
    if cleaned is not None:
        return [cleaned]
    if node.get("type") != "floating_con":
        return []

    windows: list[dict] = []
    for descendant in _identity_descendants(node):
        window = clean_tree(descendant, cache)
        if window is None or window.get("type") != "window":
            continue
        wrapper_marks = list(node.get("marks") or [])
        window_marks = list(window.get("marks") or [])
        if wrapper_marks or window_marks:
            window["marks"] = list(dict.fromkeys(wrapper_marks + window_marks))
        if node.get("border") and not window.get("border"):
            window["border"] = node["border"]
        scratchpad = node.get("scratchpad_state")
        if scratchpad not in (None, "", "none") and not window.get("scratchpad_state"):
            window["scratchpad_state"] = scratchpad
        windows.append(window)

    if windows:
        log.warning(
            "Floating group of %d windows saved as separate windows", len(windows)
        )
    return windows


def clean_tree(node: dict, cache: ProcCache) -> dict | None:
    """Convert one tree node into the portable session format.

    Return a window, container, or workspace dict, or None when the node has
    no restorable content or is a transient terminal.
    """
    ntype = node.get("type")
    source = _window_source(node)

    if source is not None and ntype in ("con", "floating_con"):
        cls = node_class(source)
        app_id = _kitty_app_id(source, node_app_id(source))
        if app_id is None:
            return None

        pid = node_pid(source)
        info: dict[str, object] = {}

        if app_id in ("kitty", "kitty_drop"):
            cwd = cache.get_terminal_cwd(pid) if pid else str(Path.home())
            zellij_sess = cache.get_zellij_session(pid) if pid else None
            is_ssh, ssh_cmd = cache.is_ssh_or_sudo(pid) if pid else (False, "")
            nvim_pid = cache.get_nvim_pid(pid) if pid else None

            if zellij_sess is not None:
                info["nvim_type"] = "none"
                info["zellij_session"] = zellij_sess
                info["cwd"] = cwd
                log.info("Kitty %s has zellij session %s", pid, zellij_sess)
            elif is_ssh:
                info["nvim_type"] = "none"
                info["was_ssh"] = ssh_cmd
                info["cwd"] = cwd
                log.info("Kitty %s is ssh/sudo (%s), saving cwd only", pid, ssh_cmd)
            elif nvim_pid is not None:
                nvim_server_pid, live_state = get_terminal_nvim_state(pid, cache)

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
            parsed = calibre_title_from_window(source.get("name", ""))
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

        percent = source.get("percent")
        window: dict[str, object] = {
            "type": "window",
            "app_id": app_id,
            "class": cls,
            "name": source.get("name", ""),
            "pid": pid,
            "fullscreen_mode": source.get("fullscreen_mode", 0),
            "rect": source.get("rect", {}),
            "marks": source.get("marks", []),
            "border": source.get("border", ""),
            "scratchpad_state": source.get("scratchpad_state", "none"),
            **info,
        }
        if isinstance(percent, (int, float)):
            window["percent"] = float(percent)
        return window

    if ntype in ("con", "workspace"):
        children = [c for n in node.get("nodes", []) if (c := clean_tree(n, cache))]
        floating: list[dict] = []
        for n in node.get("floating_nodes", []):
            floating.extend(clean_floating(n, cache))
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
