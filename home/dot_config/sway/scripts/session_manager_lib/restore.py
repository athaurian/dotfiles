"""Session restore orchestration."""

from __future__ import annotations

import json
import logging
from typing import Any

from .apps.generic import launch_and_get_id
from .apps.helium import collect_helium_nodes, get_helium_restored_id
from .background import restore_background_apps
from .config import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    SCRATCH_RESTORE_WORKSPACE,
    STATE_DIR,
    STATE_FILE,
)
from .ipc import close_connection, get_tree, run_command, run_command_logged
from .locking import operation_lock
from .logging_setup import notify
from .proc_cache import ProcCache
from .state import RestoreContext

log = logging.getLogger("session_manager")

# Log command failures but never abort the walk. Stale con_id and closed window
# failures are expected during restore.
cmd = run_command_logged


class StateValidationError(ValueError):
    """Raised when the saved restore payload is structurally invalid."""


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise StateValidationError(f"{path} must be a list")
    return value


def _validate_node(node: Any, path: str) -> None:
    if not isinstance(node, dict):
        raise StateValidationError(f"{path} must be an object")

    ntype = node.get("type")
    if ntype not in ("workspace", "con", "window"):
        raise StateValidationError(f"{path}.type is invalid or missing")

    if ntype == "window":
        if "rect" in node and not isinstance(node["rect"], dict):
            raise StateValidationError(f"{path}.rect must be an object")
        if "marks" in node:
            marks = _require_list(node["marks"], f"{path}.marks")
            if not all(isinstance(mark, str) for mark in marks):
                raise StateValidationError(f"{path}.marks must contain only strings")
        if "fullscreen_mode" in node and not isinstance(node["fullscreen_mode"], int):
            raise StateValidationError(f"{path}.fullscreen_mode must be an integer")
        if "percent" in node and not isinstance(node["percent"], (int, float)):
            raise StateValidationError(f"{path}.percent must be a number")
        return

    if ntype == "workspace" and (
        not isinstance(node.get("name"), str) or not node["name"]
    ):
        raise StateValidationError(f"{path}.name must be a non-empty string")

    # Layout is required for workspace/con because _restore_node accesses
    # node["layout"] unconditionally. clean_tree always emits this key.
    if ntype in ("workspace", "con"):
        if "layout" not in node:
            raise StateValidationError(f"{path}.layout is required")
        if not isinstance(node["layout"], str):
            raise StateValidationError(f"{path}.layout must be a string")
        if "percent" in node and not isinstance(node["percent"], (int, float)):
            raise StateValidationError(f"{path}.percent must be a number")

    for key in ("nodes", "floating_nodes"):
        children = _require_list(node.get(key, []), f"{path}.{key}")
        for index, child in enumerate(children):
            _validate_node(child, f"{path}.{key}[{index}]")


def _normalise_restore_payload(
    payload: Any,
) -> tuple[list[dict], list[dict], list[dict[str, str]] | None, str | None]:
    if isinstance(payload, list):
        workspaces = payload
        hidden_scratchpad = []
        background_apps = None
        focused_workspace = None
    elif isinstance(payload, dict):
        workspaces = payload.get("workspaces", [])
        hidden_scratchpad = payload.get("hidden_scratchpad", [])
        background_apps = payload.get("background_apps")
        focused_workspace = payload.get("focused_workspace")
        if focused_workspace is not None and (
            not isinstance(focused_workspace, str) or not focused_workspace
        ):
            raise StateValidationError("focused_workspace must be a non-empty string")
    else:
        raise StateValidationError("session payload must be an object or legacy list")

    workspace_list = _require_list(workspaces, "workspaces")
    scratchpad_list = _require_list(hidden_scratchpad, "hidden_scratchpad")

    for index, ws in enumerate(workspace_list):
        _validate_node(ws, f"workspaces[{index}]")
        if ws.get("type") != "workspace":
            raise StateValidationError(f"workspaces[{index}] must be a workspace")

    for index, node in enumerate(scratchpad_list):
        _validate_node(node, f"hidden_scratchpad[{index}]")
        if node.get("type") != "window":
            raise StateValidationError(f"hidden_scratchpad[{index}] must be a window")

    if background_apps is not None:
        apps = _require_list(background_apps, "background_apps")
        for index, app in enumerate(apps):
            if not isinstance(app, dict):
                raise StateValidationError(
                    f"background_apps[{index}] must be an object"
                )
            if "app_id" in app and not isinstance(app["app_id"], str):
                raise StateValidationError(
                    f"background_apps[{index}].app_id must be a string"
                )
        background_apps = apps

    return workspace_list, scratchpad_list, background_apps, focused_workspace


def has_restorable_content() -> bool:
    """Report whether the saved session contains anything worth restoring.

    Backs the login prompt, which stays hidden when restore would be a
    no-op. Missing, unreadable, and invalid state files count as empty,
    as does a hidden_scratchpad containing only foot_drop windows, since
    the dropdown terminal respawns on demand from its keybind.
    """
    if not STATE_FILE.exists():
        return False

    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            payload = json.load(f)
        workspaces, hidden_scratchpad, background_apps, _ = _normalise_restore_payload(
            payload
        )
    except (OSError, json.JSONDecodeError, StateValidationError) as exc:
        log.warning("Session file %s not restorable: %s", STATE_FILE, exc)
        return False

    restorable_scratchpad = [
        node for node in hidden_scratchpad if node.get("app_id") != "foot_drop"
    ]
    return bool(workspaces or restorable_scratchpad or background_apps)


def _clamp_rect_to_output(rect: dict, workspace_name: str | None = None) -> dict:
    """Clamp floating rect to stay fully inside output if off-screen.

    Saved rects are output-absolute (e.g. workspace 1 content starts at
    4,28 after bar/gaps). Clamping therefore happens in output coordinates;
    _apply_geometry converts to workspace-relative afterwards because
    `move position` anchors on the workspace content origin (live probe:
    `move position 100 100` lands at output 104,128 on a 4,28 workspace).
    """
    try:
        tree = get_tree()
        target_rect = None
        for out in tree.get("nodes", []):
            if (
                out.get("type") == "output"
                and out.get("name") != "__i3"
                and out.get("active")
            ):
                target_rect = out.get("rect")
                if target_rect:
                    break
        if not target_rect:
            target_rect = {"x": 0, "y": 0, "width": 1920, "height": 1080}
        x = int(rect.get("x", 0))
        y = int(rect.get("y", 0))
        w = int(rect.get("width", DEFAULT_WINDOW_WIDTH))
        h = int(rect.get("height", DEFAULT_WINDOW_HEIGHT))
        max_x = target_rect["x"] + target_rect["width"] - w
        max_y = target_rect["y"] + target_rect["height"] - h
        clamped_x = max(target_rect["x"], min(x, max_x))
        clamped_y = max(target_rect["y"], min(y, max_y))
        if clamped_x != x or clamped_y != y:
            log.info(
                "Clamped floating rect %s -> (%d,%d) to fit output %s",
                rect,
                clamped_x,
                clamped_y,
                target_rect,
            )
            return {"x": clamped_x, "y": clamped_y, "width": w, "height": h}
        return rect
    except (OSError, ValueError, KeyError):
        return rect


def _workspace_origin(workspace_name: str | None) -> tuple[int, int]:
    """Top-left of a workspace in output coordinates.

    Falls back to (0, 0) — the old behaviour — when the workspace cannot
    be found (e.g. in unit tests or if it was never created).
    """
    if not workspace_name:
        return (0, 0)
    try:
        tree = get_tree()
    except OSError:
        return (0, 0)
    for out in tree.get("nodes", []):
        for ws in out.get("nodes", []):
            if ws.get("type") == "workspace" and ws.get("name") == workspace_name:
                rect = ws.get("rect", {})
                try:
                    return (int(rect.get("x", 0)), int(rect.get("y", 0)))
                except (ValueError, TypeError):
                    return (0, 0)
    return (0, 0)


def _live_deco_height(win_id: int) -> int:
    """Live titlebar height of a window, or 0 for border styles without one.

    With `border normal`, `move position` anchors on the decoration
    top-left (live probe: requesting 100,100 places deco at 100,100 and the
    content rect 26px below), so the content lands exactly on the saved
    position only when this height is subtracted from the target y.
    Pixel borders report a zero-height deco_rect and are unaffected.
    """
    try:
        tree = get_tree()
    except OSError:
        return 0

    def _find(node: dict) -> dict | None:
        if node.get("id") == win_id:
            return node
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            found = _find(child)
            if found is not None:
                return found
        return None

    try:
        node = _find(tree)
        if not node:
            return 0
        return int(node.get("deco_rect", {}).get("height", 0) or 0)
    except (ValueError, TypeError, AttributeError):
        return 0


def _apply_geometry(win_id: int, rect: dict, workspace_name: str | None = None) -> None:
    rect = _clamp_rect_to_output(rect, workspace_name)
    # Queried before resize: callers set the border first, so a `border
    # normal` titlebar is already present. `resize set` budgets that titlebar
    # inside the requested height (live probe: requesting 300 yields a 274
    # content rect under a 26 titlebar), so the saved content height is
    # restored exactly only when the titlebar is added back on top.
    deco_height = _live_deco_height(win_id)
    width = rect.get("width", DEFAULT_WINDOW_WIDTH)
    try:
        height = int(rect.get("height", DEFAULT_WINDOW_HEIGHT)) + deco_height
    except (ValueError, TypeError):
        height = rect.get("height", DEFAULT_WINDOW_HEIGHT)
    # Resize first: growing the window can shift its position, so the move
    # must come last (same order as the toggle scripts' resize-then-center).
    cmd(f"[con_id={win_id}] resize set width {width} px height {height} px")
    origin_x, origin_y = _workspace_origin(workspace_name)
    try:
        x = int(rect.get("x", 0)) - origin_x
        y = int(rect.get("y", 0)) - origin_y - deco_height
    except (ValueError, TypeError):
        x, y = rect.get("x", 0), rect.get("y", 0)
    cmd(f"[con_id={win_id}] move position {x} {y}")


def _apply_marks(win_id: int, marks: list[str]) -> None:
    for mark in marks:
        cmd(f"[con_id={win_id}] mark {mark}")


def _apply_fullscreen(win_id: int, fullscreen_mode: int) -> None:
    if fullscreen_mode == 1:
        cmd(f"[con_id={win_id}] fullscreen")


def _apply_percent(win_id: int, percent: float | None, parent_layout: str) -> None:
    if percent is None or not isinstance(percent, (int, float)):
        return
    # Skip single-window or nearly 100% — nothing to resize and sway returns parse error
    if float(percent) >= 0.99 or float(percent) <= 0.01:
        return
    ppt = round(float(percent) * 100)
    if ppt <= 0 or ppt >= 100:
        return
    if parent_layout == "splitv":
        cmd(f"[con_id={win_id}] resize set height {ppt} ppt")
    elif parent_layout == "splith":
        cmd(f"[con_id={win_id}] resize set width {ppt} ppt")
    elif parent_layout in ("tabbed", "stacking"):
        return
    else:
        cmd(f"[con_id={win_id}] resize set width {ppt} ppt")


def _layout_cmd(layout: str) -> str:
    # Sway tree reports "stacked" but the command is "stacking".
    return "stacking" if layout == "stacked" else layout


def _resolve_window(node: dict, ctx: RestoreContext) -> int | None:
    app_id = node.get("app_id", "")
    if app_id == "helium":
        return get_helium_restored_id(node, ctx)
    return launch_and_get_id(node, ctx.claimed_ids)


def _restore_floating(node: dict, ctx: RestoreContext) -> None:
    if node["type"] != "window":
        return
    app_id = node.get("app_id", "")
    win_id = _resolve_window(node, ctx)
    if not win_id:
        return

    _apply_marks(win_id, node.get("marks", []))

    rect = node.get("rect", {})
    fullscreen_mode = node.get("fullscreen_mode", 0)
    scratchpad_state = node.get("scratchpad_state", "none")

    if app_id == "foot_drop":
        _apply_geometry(win_id, rect, ctx.current_workspace)
        _apply_fullscreen(win_id, fullscreen_mode)
        return

    if app_id != "helium" and scratchpad_state != "none":
        cmd(f"[con_id={win_id}] floating enable")
        cmd(f"[con_id={win_id}] border normal")
        cmd(f"[con_id={win_id}] move scratchpad")
        cmd(f"[con_id={win_id}] scratchpad show")
        _apply_geometry(win_id, rect, ctx.current_workspace)
        _apply_fullscreen(win_id, fullscreen_mode)
        return

    if app_id == "helium" and ctx.current_workspace:
        cmd(f"[con_id={win_id}] move to workspace {ctx.current_workspace}")
    cmd(f"[con_id={win_id}] floating enable")

    _apply_geometry(win_id, rect, ctx.current_workspace)
    _apply_fullscreen(win_id, fullscreen_mode)


def _restore_hidden_scratchpad(node: dict, ctx: RestoreContext) -> None:
    if node.get("type") != "window":
        return
    app_id = node.get("app_id", "")
    win_id = _resolve_window(node, ctx)
    if not win_id:
        return

    if app_id == "foot_drop":
        # Dropdown is always scratchpad; no geometry/marks needed.
        cmd(f"[con_id={win_id}] move scratchpad")
        return

    _apply_marks(win_id, node.get("marks", []))
    cmd(f"[con_id={win_id}] floating enable")
    cmd(f"[con_id={win_id}] border normal")
    # Geometry is applied while the window sits on SCRATCH_RESTORE_WORKSPACE
    # (callers switch there first); its origin matches a normal workspace on
    # the same output, so the saved output-absolute rect converts correctly
    # and survives the later `scratchpad show` on any same-output workspace.
    _apply_geometry(win_id, node.get("rect", {}), SCRATCH_RESTORE_WORKSPACE)
    cmd(f"[con_id={win_id}] move scratchpad")


def _restore_node(
    node: dict, ctx: RestoreContext, parent_layout: str | None = None
) -> None:
    ntype = node["type"]

    if ntype == "workspace":
        ctx.current_workspace = node["name"]
        cmd(f"workspace {node['name']}")
        # Focus parent so `layout` targets the workspace even if a floating
        # window is focused; silent variant avoids noise when already focused.
        run_command("focus parent")
        cmd(f"layout {_layout_cmd(node['layout'])}")
        for child in node.get("nodes", []):
            cmd(f"workspace {node['name']}")
            _restore_node(child, ctx, parent_layout=node["layout"])
        for child in node.get("floating_nodes", []):
            cmd(f"workspace {node['name']}")
            _restore_floating(child, ctx)

    elif ntype == "con":
        children = node.get("nodes", [])
        if children:
            _restore_node(children[0], ctx, parent_layout=node["layout"])
            orientation = "v" if node["layout"] == "splitv" else "h"
            cmd(f"split {orientation}")
            cmd(f"layout {_layout_cmd(node['layout'])}")
            for child in children[1:]:
                _restore_node(child, ctx, parent_layout=node["layout"])
        for child in node.get("floating_nodes", []):
            _restore_floating(child, ctx)

    elif ntype == "window":
        app_id = node.get("app_id", "")
        win_id = _resolve_window(node, ctx)
        if not win_id:
            return
        _apply_marks(win_id, node.get("marks", []))
        if app_id == "helium" and ctx.current_workspace:
            cmd(f"[con_id={win_id}] move to workspace {ctx.current_workspace}")
        cmd(f"[con_id={win_id}] focus")
        _apply_fullscreen(win_id, node.get("fullscreen_mode", 0))
        _apply_percent(win_id, node.get("percent"), parent_layout or "")


def restore_session(
    *, notify_user: bool = True, workspace_filter: str | None = None
) -> None:
    """Restore the previously saved Sway session.

    Acquires the interprocess operation lock to serialize against concurrent
    save/restore invocations (for example, from power-control bindings), then hands
    off to _restore_session_locked() to perform the actual restoration.
    """
    if not STATE_FILE.exists():
        log.info("No session file found.")
        return

    with operation_lock(STATE_DIR):
        _restore_session_locked(
            notify_user=notify_user, workspace_filter=workspace_filter
        )


def diff_sessions() -> None:
    """Show a plain-English diff of live vs saved session."""
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            payload = json.load(f)
        saved_ws, saved_hidden, saved_bg, _ = _normalise_restore_payload(payload)
    except (OSError, json.JSONDecodeError, StateValidationError) as exc:
        print(f"Saved session unreadable: {exc}")
        return

    try:
        live_tree = get_tree()
    except OSError as exc:
        print(f"Cannot read live tree: {exc}")
        return
    finally:
        try:
            close_connection()
        except OSError:
            pass

    # Count live workspaces/windows
    live_ws = {}
    for out in live_tree.get("nodes", []):
        for ws in out.get("nodes", []):
            if ws.get("type") != "workspace" or ws.get("name") == "__i3_scratch":
                continue
            name = ws.get("name")
            count = 0

            def cnt_live(node: dict) -> int:
                if node.get("type") == "window":
                    return 1
                if node.get("type") in ("con", "floating_con") and node.get("app_id"):
                    return 1
                s = 0
                for c in node.get("nodes", []):
                    s += cnt_live(c)
                for c in node.get("floating_nodes", []):
                    s += cnt_live(c)
                return s

            for n in ws.get("nodes", []):
                count += cnt_live(n)
            for n in ws.get("floating_nodes", []):
                count += cnt_live(n)
            live_ws[name] = count

    saved_ws_map: dict[str, dict] = {
        ws["name"]: ws for ws in saved_ws if ws.get("name")
    }
    print("Live vs Saved diff:")
    all_names = sorted(set(live_ws) | set(saved_ws_map))
    for name in all_names:
        live_c = live_ws.get(name)
        saved = saved_ws_map.get(name)
        if saved:
            # Count saved windows with the same predicate as the live count in the preceding block.
            def scnt(node: dict) -> int:
                if node.get("type") == "window":
                    return 1
                if node.get("type") in ("con", "floating_con") and node.get("app_id"):
                    return 1
                s = 0
                for c in node.get("nodes", []):
                    s += scnt(c)
                for c in node.get("floating_nodes", []):
                    s += scnt(c)
                return s

            saved_c = sum(scnt(n) for n in saved.get("nodes", [])) + sum(
                scnt(n) for n in saved.get("floating_nodes", [])
            )
        else:
            saved_c = None
        if live_c is None:
            print(f"  ws {name}: would create {saved_c} windows (currently missing)")
        elif saved_c is None:
            print(f"  ws {name}: {live_c} live windows would remain (not in saved)")
        elif live_c == saved_c:
            print(f"  ws {name}: {live_c} windows matches saved")
        else:
            print(f"  ws {name}: live {live_c} vs saved {saved_c} would recreate")

    if saved_hidden:
        print(f"  hidden scratchpad: {len(saved_hidden)} windows saved")
    if saved_bg:
        print(f"  background apps: {len(saved_bg)} saved")

    if not saved_ws and not saved_hidden:
        print("  Saved session is empty")


def _restore_session_locked(
    *, notify_user: bool = True, workspace_filter: str | None = None
) -> None:
    """Perform the actual session restoration under the operation lock."""
    if not STATE_FILE.exists():
        log.info("No session file found.")
        return

    def _notify(msg: str, **kw) -> None:
        if notify_user:
            notify(msg, **kw)

    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            payload = json.load(f)
        workspaces, hidden_scratchpad, background_apps, focused_workspace = (
            _normalise_restore_payload(payload)
        )
        if workspace_filter:
            orig = len(workspaces)
            workspaces = [ws for ws in workspaces if ws.get("name") == workspace_filter]
            if not workspaces:
                _notify(
                    f"workspace {workspace_filter} not in saved session",
                    urgency="normal",
                )
                log.warning(
                    "Workspace filter %s not found in %s", workspace_filter, STATE_FILE
                )
                return
            hidden_scratchpad = []
            background_apps = None
            log.info(
                "Restoring only workspace %s (%d/%d)",
                workspace_filter,
                len(workspaces),
                orig,
            )
            _notify(
                f"restoring only workspace {workspace_filter}...",
                urgency="critical",
                timeout_ms=0,
            )
    except (OSError, json.JSONDecodeError, StateValidationError) as exc:
        _notify("session restore skipped: invalid session file", urgency="normal")
        log.warning("Invalid session file %s: %s", STATE_FILE, exc)
        return

    ctx = RestoreContext()
    partial_failures: list[str] = []

    try:
        _notify(
            "<b>don't move!</b> restoring previous session...",
            timeout_ms=0,
            urgency="critical",
        )

        for ws in workspaces:
            collect_helium_nodes(ws, ctx)

        for node in hidden_scratchpad:
            collect_helium_nodes(node, ctx)

        for ws in workspaces:
            try:
                _restore_node(ws, ctx)
            except Exception as exc:
                partial_failures.append(f"{ws.get('name', '?')}: {exc}")
                log.exception("Partial restore failure in workspace %s", ws.get("name"))

        if hidden_scratchpad:
            cmd(f"workspace {SCRATCH_RESTORE_WORKSPACE}")
            for node in hidden_scratchpad:
                try:
                    _restore_hidden_scratchpad(node, ctx)
                except Exception as exc:
                    partial_failures.append(f"hidden scratchpad: {exc}")
                    log.exception("Failed to restore hidden scratchpad window")

        restore_background_apps(
            background_apps,
            cache=ProcCache.snapshot() if background_apps else None,
        )
        cmd(f"workspace {focused_workspace}" if focused_workspace else "workspace 1")

    except Exception:
        _notify("session restore failed")
        log.exception("Session restore failed.")
        raise
    finally:
        close_connection()

    message = "<b>session restored successfully.</b>"
    if partial_failures:
        _notify(
            f"{message} Partial failures: {len(partial_failures)}. See logs.",
            urgency="normal",
        )
        log.warning("Partial restore failures: %s", ", ".join(partial_failures))
    else:
        _notify(f"{message} you can safely move now.")
    log.info("Restore complete.")
