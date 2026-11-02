"""Session restore orchestration."""

from __future__ import annotations

import json
import logging
import math
import re
import time
from typing import Any

from .apps.generic import launch_and_get_id
from .apps.helium import collect_helium_nodes, get_helium_restored_id
from .background import restore_background_apps
from .config import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    FLOAT_GEOMETRY_RETRY_DELAY,
    SCRATCH_RESTORE_WORKSPACE,
    SCRATCHPAD_WORKSPACE,
    STATE_DIR,
    STATE_FILE,
    detect_backend,
)
from .ipc import (
    close_connection,
    get_tree,
    node_app_id,
    run_command,
    run_command_logged,
    walk_tree,
)
from .locking import operation_lock
from .logging_setup import notify
from .proc_cache import ProcCache
from .session_env import apply_compositor_env
from .state import RestoreContext

log = logging.getLogger("session_manager")

# Log command failures but never abort the walk. Stale con_id and closed window
# failures are expected during restore.
cmd = run_command_logged

# Patched in tests so the geometry settle delay does not slow the suite down.
sleep = time.sleep

_WORKSPACE_SAFE = re.compile(r"^[A-Za-z0-9_.:-]+$")

# Marks are plain identifiers, so anything else is refused rather than
# quoted into the compositor command language.
_MARK_SAFE = re.compile(r"^[A-Za-z0-9_.:-]+$")

# Layout names each compositor accepts in its `layout` command. i3 and Sway
# disagree: Sway has no "stacked" command and i3 has no "tiling"/"floating".
_LAYOUTS: dict[str, frozenset[str]] = {
    "i3": frozenset(
        {"default", "stacked", "stacking", "tabbed", "splitv", "splith", "toggle"}
    ),
    "sway": frozenset({"default", "stacking", "tabbed", "splitv", "splith", "toggle"}),
}


def _quote_token(name: str) -> str:
    """Quote a name for the compositor command language when it needs it."""
    if _WORKSPACE_SAFE.match(name):
        return name
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _workspace_cmd(name: str) -> str:
    """Build a workspace command, quoting names that contain separators."""
    return f"workspace {_quote_token(name)}"


def _move_to_workspace_cmd(win_id: int, name: str) -> str:
    """Build a command that moves a window to a named workspace."""
    return f"[con_id={win_id}] move to workspace {_quote_token(name)}"


def _rect_number(rect: dict, key: str, default: int) -> int:
    """Return a rect member as a plain int.

    Only finite numbers are accepted. Everything else falls back to the
    default, so a malformed state file can never put arbitrary text into a
    compositor command.
    """
    value = rect.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    try:
        if not math.isfinite(value):
            return default
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


class StateValidationError(ValueError):
    """Raised when the saved restore payload is structurally invalid."""


def _require_list(value: Any, path: str) -> list[Any]:
    """Return a list value, or raise when the type is wrong."""
    if not isinstance(value, list):
        raise StateValidationError(f"{path} must be a list")
    return value


def _validate_rect(rect: dict, path: str) -> None:
    """Reject rect members that are not finite numbers."""
    for key in ("x", "y", "width", "height"):
        if key not in rect:
            continue
        value = rect[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise StateValidationError(f"{path}.{key} must be a number")
        if not math.isfinite(value):
            raise StateValidationError(f"{path}.{key} must be a finite number")


def _validate_node(node: Any, path: str) -> None:
    """Validate a saved tree node and its children."""
    if not isinstance(node, dict):
        raise StateValidationError(f"{path} must be an object")

    ntype = node.get("type")
    if ntype not in ("workspace", "con", "window"):
        raise StateValidationError(f"{path}.type is invalid or missing")

    if ntype == "window":
        if "rect" in node and not isinstance(node["rect"], dict):
            raise StateValidationError(f"{path}.rect must be an object")
        if isinstance(node.get("rect"), dict):
            _validate_rect(node["rect"], f"{path}.rect")
        if "marks" in node:
            marks = _require_list(node["marks"], f"{path}.marks")
            if not all(isinstance(mark, str) for mark in marks):
                raise StateValidationError(f"{path}.marks must contain only strings")
        if "fullscreen_mode" in node and not isinstance(node["fullscreen_mode"], int):
            raise StateValidationError(f"{path}.fullscreen_mode must be an integer")
        if "percent" in node and not isinstance(node["percent"], (int, float)):
            raise StateValidationError(f"{path}.percent must be a number")
        if "percent" in node and not math.isfinite(node["percent"]):
            raise StateValidationError(f"{path}.percent must be a finite number")
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
        if "percent" in node and not math.isfinite(node["percent"]):
            raise StateValidationError(f"{path}.percent must be a finite number")

    for key in ("nodes", "floating_nodes"):
        children = _require_list(node.get(key, []), f"{path}.{key}")
        for index, child in enumerate(children):
            _validate_node(child, f"{path}.{key}[{index}]")


def _normalise_restore_payload(
    payload: Any,
) -> tuple[list[dict], list[dict], list[dict[str, str]] | None, str | None]:
    """Return saved workspaces, scratchpad, background apps, and focus.

    Accept both the current object payload and the legacy list of
    workspaces.
    """
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
    as does a hidden_scratchpad containing only kitty_drop windows, since
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
        node for node in hidden_scratchpad if node.get("app_id") != "kitty_drop"
    ]
    return bool(workspaces or restorable_scratchpad or background_apps)


def _output_contains(out: dict, x: int, y: int) -> bool:
    """Report whether a point lies inside an output rect."""
    ox = _rect_number(out, "x", 0)
    oy = _rect_number(out, "y", 0)
    ow = _rect_number(out, "width", 0)
    oh = _rect_number(out, "height", 0)
    return ox <= x < ox + ow and oy <= y < oy + oh


def _active_output_rects(tree: dict) -> list[dict]:
    """Return the rects of the active outputs."""
    rects = []
    for out in tree.get("nodes", []):
        if out.get("type") != "output" or out.get("name") == "__i3":
            continue
        if not out.get("active"):
            continue
        rect = out.get("rect")
        if isinstance(rect, dict) and rect.get("width") and rect.get("height"):
            rects.append(rect)
    return rects


def _output_rect_for(tree: dict, rect: dict, workspace_name: str | None) -> dict | None:
    """Pick the output a saved floating rect belongs to.

    Saved rects are output-absolute, so the output holding the window's
    centre is the one it was saved on. When the window sat outside every
    output, the output that hosts the workspace is used instead.
    """
    outputs = _active_output_rects(tree)
    if not outputs:
        return None

    x = _rect_number(rect, "x", 0)
    y = _rect_number(rect, "y", 0)
    w = _rect_number(rect, "width", DEFAULT_WINDOW_WIDTH)
    h = _rect_number(rect, "height", DEFAULT_WINDOW_HEIGHT)
    for out in outputs:
        if _output_contains(out, x + w // 2, y + h // 2):
            return out

    if workspace_name:
        for ws in walk_tree(tree):
            if ws.get("type") != "workspace" or ws.get("name") != workspace_name:
                continue
            ws_rect = ws.get("rect")
            if isinstance(ws_rect, dict):
                wx = _rect_number(ws_rect, "x", 0)
                wy = _rect_number(ws_rect, "y", 0)
                for out in outputs:
                    if _output_contains(out, wx, wy):
                        return out
            break
    return outputs[0]


def _clamp_rect_to_output(rect: dict, workspace_name: str | None = None) -> dict:
    """Clamp the floating rect to stay fully inside the output when off-screen.

    Saved rects are output-absolute (for example, workspace 1 content can
    start at 4,28 after bars and gaps). Clamping therefore happens in output
    coordinates. On Sway, `_apply_geometry` converts the result to
    workspace-relative coordinates because `move position` anchors on the
    workspace content origin. i3's `move position` is already
    output-absolute, so the clamped rect is used as-is.

    Args:
        rect: Floating rect with x, y, width, and height.
        workspace_name: Workspace the rect belongs to. It names the output
            to clamp against when the rect itself sits outside every
            output.

    Returns:
        The clamped rect, or the original rect when clamping is
        impossible.
    """
    try:
        tree = get_tree()
        target_rect = _output_rect_for(tree, rect, workspace_name)
        if not target_rect:
            target_rect = {"x": 0, "y": 0, "width": 1920, "height": 1080}
        x = _rect_number(rect, "x", 0)
        y = _rect_number(rect, "y", 0)
        w = _rect_number(rect, "width", DEFAULT_WINDOW_WIDTH)
        h = _rect_number(rect, "height", DEFAULT_WINDOW_HEIGHT)
        max_x = (
            _rect_number(target_rect, "x", 0)
            + _rect_number(target_rect, "width", 1920)
            - w
        )
        max_y = (
            _rect_number(target_rect, "y", 0)
            + _rect_number(target_rect, "height", 1080)
            - h
        )
        clamped_x = max(_rect_number(target_rect, "x", 0), min(x, max_x))
        clamped_y = max(_rect_number(target_rect, "y", 0), min(y, max_y))
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
    """Return the top-left of a workspace in output coordinates.

    Fall back to (0, 0) when the workspace cannot be found or does not
    exist yet. i3's `move position` is already output-absolute, so it
    always uses (0, 0).

    Args:
        workspace_name: Name of the workspace to locate, or None.

    Returns:
        The (x, y) origin, or (0, 0) when the workspace cannot be
        found.
    """
    if not workspace_name or detect_backend() == "i3":
        return (0, 0)
    try:
        tree = get_tree()
    except OSError:
        return (0, 0)
    for ws in walk_tree(tree):
        if ws.get("type") == "workspace" and ws.get("name") == workspace_name:
            rect = ws.get("rect", {})
            try:
                return (int(rect.get("x", 0)), int(rect.get("y", 0)))
            except (ValueError, TypeError):
                return (0, 0)
    return (0, 0)


def _live_deco_height(win_id: int) -> int:
    """Return the live titlebar height of a window, or 0 for border styles
    without one.

    With `border normal`, `move position` anchors on the decoration
    top-left, so the content lands exactly on the saved position only when
    this height is subtracted from the target y. Pixel borders report a
    zero-height deco_rect and are unaffected.

    Args:
        win_id: Sway container id of the window to inspect.

    Returns:
        The decoration height, or 0 when the window has no titlebar or
        cannot be found.
    """
    try:
        tree = get_tree()
    except OSError:
        return 0

    def _find(node: dict) -> dict | None:
        """Find a node by container id, depth-first."""
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


def _apply_sway_geometry(win_id: int, rect: dict, workspace_name: str | None) -> None:
    """Apply a saved rect to a floating Sway window.

    Sway anchors `move position` on the decoration and budgets the titlebar
    inside the height passed to `resize set`. Add the measured decoration
    height back so the saved content rect is restored exactly.

    Args:
        win_id: Sway container id of the window.
        rect: The saved rect, already clamped to an output.
        workspace_name: The workspace the window is on, used to turn the
            output-absolute rect into Sway's workspace-relative one.
    """
    deco_height = _live_deco_height(win_id)
    width = _rect_number(rect, "width", DEFAULT_WINDOW_WIDTH)
    height = _rect_number(rect, "height", DEFAULT_WINDOW_HEIGHT) + deco_height
    # Resize before moving: growing the window can shift its position, so
    # the move must come last.
    cmd(f"[con_id={win_id}] resize set width {width} px height {height} px")
    origin_x, origin_y = _workspace_origin(workspace_name)
    x = _rect_number(rect, "x", 0) - origin_x
    y = _rect_number(rect, "y", 0) - origin_y - deco_height
    cmd(f"[con_id={win_id}] move position {x} {y}")


def _apply_geometry(win_id: int, rect: dict, workspace_name: str | None = None) -> None:
    """Apply saved geometry to a window, clamped to its output."""
    rect = _clamp_rect_to_output(rect, workspace_name)
    backend = detect_backend()

    if backend == "i3":
        # i3 takes `move position` and `resize set` as output-absolute, and
        # `resize set height` includes the titlebar in the requested height.
        # No workspace-origin or titlebar offset is needed.
        width = _rect_number(rect, "width", DEFAULT_WINDOW_WIDTH)
        height = _rect_number(rect, "height", DEFAULT_WINDOW_HEIGHT)
        cmd(f"[con_id={win_id}] resize set width {width} px height {height} px")
        x = _rect_number(rect, "x", 0)
        y = _rect_number(rect, "y", 0)
        cmd(f"[con_id={win_id}] move position {x} {y}")
        return

    # A newly started window can ask Sway for its own size after the resize
    # and undo it. It may also lack a titlebar until it settles, so the
    # decoration height cannot be measured yet. Apply the geometry again
    # after the delay to cover both cases. i3 applies geometry directly and
    # returns above without waiting.
    _apply_sway_geometry(win_id, rect, workspace_name)
    sleep(FLOAT_GEOMETRY_RETRY_DELAY)
    _apply_sway_geometry(win_id, rect, workspace_name)


def _apply_marks(win_id: int, marks: list[str]) -> None:
    """Apply saved marks to a window."""
    for mark in marks:
        if not _MARK_SAFE.match(mark):
            log.warning("skipping mark with unsupported characters: %r", mark)
            continue
        cmd(f"[con_id={win_id}] mark {mark}")


def _apply_fullscreen(win_id: int, fullscreen_mode: int) -> None:
    """Apply saved fullscreen state to a window."""
    if fullscreen_mode == 1:
        cmd(f"[con_id={win_id}] fullscreen")


def _apply_border(win_id: int, border: str) -> None:
    """Apply a saved floating border style (Sway and i3 names match)."""
    if border in ("normal", "pixel", "none"):
        cmd(f"[con_id={win_id}] border {border}")


def _apply_percent(win_id: int, percent: float | None, parent_layout: str) -> None:
    """Restore a window's share of its parent split."""
    if percent is None or isinstance(percent, bool):
        return
    if not isinstance(percent, (int, float)) or not math.isfinite(percent):
        return
    # Skip shares near 0 or 1, including single-window splits. There is
    # nothing to resize, and sway returns a parse error for those values.
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
    """Return the layout name to send, or an empty string to skip it.

    Sway's tree reports "stacked" but its command is "stacking". Both
    compositors reject names they do not know, so the name is checked
    against the ones the running compositor accepts.
    """
    name = "stacking" if layout == "stacked" else layout
    allowed = _LAYOUTS.get(detect_backend(), _LAYOUTS["sway"])
    if name not in allowed:
        log.warning("skipping unsupported layout %r", layout)
        return ""
    return name


def _apply_layout(layout: str) -> None:
    """Apply a container layout when the compositor supports it."""
    name = _layout_cmd(layout)
    if name:
        cmd(f"layout {name}")


def _resolve_window(node: dict, ctx: RestoreContext) -> int | None:
    """Launch or locate the window for a saved node."""
    if node_app_id(node) == "helium":
        return get_helium_restored_id(node, ctx)
    return launch_and_get_id(node, ctx.claimed_ids)


def _record_missing(ctx: RestoreContext, node: dict) -> None:
    """Record a saved window that did not come back."""
    if node_app_id(node) == "kitty_drop":
        # The dropdown terminal is spawned by its own keybinding on demand.
        return
    ctx.missing.append(_failure_label(node))


def _restore_floating(node: dict, ctx: RestoreContext) -> None:
    """Restore one floating window."""
    if node["type"] != "window":
        return
    app_id = node_app_id(node)
    win_id = _resolve_window(node, ctx)
    if not win_id:
        _record_missing(ctx, node)
        return

    _apply_marks(win_id, node.get("marks", []))

    rect = node.get("rect", {})
    fullscreen_mode = node.get("fullscreen_mode", 0)
    scratchpad_state = node.get("scratchpad_state", "none")

    if app_id == "kitty_drop":
        _apply_geometry(win_id, rect, ctx.current_workspace)
        _apply_fullscreen(win_id, fullscreen_mode)
        return

    if app_id != "helium" and scratchpad_state != "none":
        cmd(f"[con_id={win_id}] floating enable")
        _apply_border(win_id, node.get("border") or "normal")
        cmd(f"[con_id={win_id}] move scratchpad")
        cmd(f"[con_id={win_id}] scratchpad show")
        _apply_geometry(win_id, rect, ctx.current_workspace)
        _apply_fullscreen(win_id, fullscreen_mode)
        return

    if app_id == "helium" and ctx.current_workspace:
        cmd(_move_to_workspace_cmd(win_id, ctx.current_workspace))
    cmd(f"[con_id={win_id}] floating enable")
    _apply_border(win_id, node.get("border", ""))

    _apply_geometry(win_id, rect, ctx.current_workspace)
    _apply_fullscreen(win_id, fullscreen_mode)


def _restore_hidden_scratchpad(node: dict, ctx: RestoreContext) -> None:
    """Restore one hidden scratchpad window and park it out of sight."""
    if node.get("type") != "window":
        return
    app_id = node_app_id(node)
    win_id = _resolve_window(node, ctx)
    if not win_id:
        _record_missing(ctx, node)
        return

    if app_id == "kitty_drop":
        # Dropdown is always scratchpad; restore its mark and border so the
        # keybind can find it again, then park it out of sight.
        _apply_marks(win_id, node.get("marks", []))
        _apply_border(win_id, node.get("border", "normal"))
        cmd(f"[con_id={win_id}] move scratchpad")
        return

    _apply_marks(win_id, node.get("marks", []))
    cmd(f"[con_id={win_id}] floating enable")
    # Older state files predate the saved border, so fall back to the
    # chromed style those windows were restored with.
    _apply_border(win_id, node.get("border") or "normal")
    # Geometry is applied on the current staging workspace, whose origin
    # matches a normal workspace on the same output. i3 refuses to switch to
    # SCRATCH_RESTORE_WORKSPACE because it is an internal name, so on i3 the
    # caller stays on the restored workspace and passes it through ctx below.
    staging = (
        SCRATCH_RESTORE_WORKSPACE if detect_backend() != "i3" else ctx.current_workspace
    )
    _apply_geometry(win_id, node.get("rect", {}), staging)
    cmd(f"[con_id={win_id}] move scratchpad")


def _failure_label(node: dict) -> str:
    """Return a readable name for a window that failed to restore."""
    return str(node.get("name") or node_app_id(node) or node.get("type", "window"))


def _record_failure(ctx: RestoreContext, node: dict, exc: Exception) -> None:
    """Record a failed window so the rest of the session still restores."""
    ctx.failures.append(f"{_failure_label(node)}: {exc}")


def _restore_child(
    node: dict, ctx: RestoreContext, parent_layout: str | None = None
) -> None:
    """Restore one tiled child, keeping a failure local to that child."""
    try:
        _restore_node(node, ctx, parent_layout=parent_layout)
    except Exception as exc:
        log.exception("Failed to restore %s", _failure_label(node))
        _record_failure(ctx, node, exc)


def _restore_floating_child(node: dict, ctx: RestoreContext) -> None:
    """Restore one floating child, keeping a failure local to that child."""
    try:
        _restore_floating(node, ctx)
    except Exception as exc:
        log.exception("Failed to restore %s", _failure_label(node))
        _record_failure(ctx, node, exc)


def _restore_node(
    node: dict, ctx: RestoreContext, parent_layout: str | None = None
) -> None:
    """Restore a saved workspace, container, or window node."""
    ntype = node["type"]

    if ntype == "workspace":
        ctx.current_workspace = node["name"]
        cmd(_workspace_cmd(node["name"]))
        # Focus parent so `layout` targets the workspace even if a floating
        # window is focused; silent variant avoids noise when already focused.
        run_command("focus parent")
        _apply_layout(node["layout"])
        for child in node.get("nodes", []):
            cmd(_workspace_cmd(node["name"]))
            _restore_child(child, ctx, parent_layout=node["layout"])
        for child in node.get("floating_nodes", []):
            cmd(_workspace_cmd(node["name"]))
            _restore_floating_child(child, ctx)

    elif ntype == "con":
        children = node.get("nodes", [])
        if children:
            _restore_child(children[0], ctx, parent_layout=node["layout"])
            orientation = "v" if node["layout"] == "splitv" else "h"
            cmd(f"split {orientation}")
            _apply_layout(node["layout"])
            for child in children[1:]:
                _restore_child(child, ctx, parent_layout=node["layout"])
        for child in node.get("floating_nodes", []):
            _restore_floating_child(child, ctx)

    elif ntype == "window":
        app_id = node_app_id(node)
        win_id = _resolve_window(node, ctx)
        if not win_id:
            _record_missing(ctx, node)
            return
        _apply_marks(win_id, node.get("marks", []))
        if app_id == "helium" and ctx.current_workspace:
            cmd(_move_to_workspace_cmd(win_id, ctx.current_workspace))
        cmd(f"[con_id={win_id}] focus")
        _apply_fullscreen(win_id, node.get("fullscreen_mode", 0))
        _apply_percent(win_id, node.get("percent"), parent_layout or "")


def restore_session(
    *, notify_user: bool = True, workspace_filter: str | None = None
) -> None:
    """Restore the previously saved Sway/i3 session.

    Acquire the interprocess operation lock to serialize against
    concurrent save/restore invocations (for example, from power-control
    bindings), then hand off to _restore_session_locked().

    Args:
        notify_user: Whether to show desktop notifications.
        workspace_filter: Restores only this workspace when set,
            otherwise restores everything.
    """
    if not STATE_FILE.exists():
        log.info("No session file found.")
        return

    # Fill in the compositor's display variables before any app is launched.
    # A restore triggered from a login script or a systemd unit can run
    # without them, and the apps would then fail to reach the display server.
    apply_compositor_env()

    # Check that the compositor is reachable before touching anything.
    # Without this, every window would fail one by one and the user would
    # see a traceback per window instead of one clear message.
    try:
        get_tree()
    except OSError as exc:
        log.warning("Cannot reach the window manager: %s", exc)
        if notify_user:
            notify("session restore failed: cannot reach the window manager")
        raise

    with operation_lock(STATE_DIR):
        _restore_session_locked(
            notify_user=notify_user, workspace_filter=workspace_filter
        )


def diff_sessions() -> None:
    """Show a plain-English diff of the live and saved sessions."""
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

    live_ws: dict[str, int] = {}
    for ws in walk_tree(live_tree):
        if ws.get("type") != "workspace" or ws.get("name") == SCRATCHPAD_WORKSPACE:
            continue
        name = ws.get("name")
        if not isinstance(name, str):
            continue
        count = 0

        def cnt_live(node: dict) -> int:
            """Count live windows under a node."""
            if node.get("type") == "window":
                return 1
            if node.get("type") in ("con", "floating_con") and node_app_id(node):
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
        ws["name"]: ws for ws in saved_ws if isinstance(ws.get("name"), str)
    }
    print("Live vs Saved diff:")
    all_names = sorted(set(live_ws) | set(saved_ws_map))
    for name in all_names:
        live_c = live_ws.get(name)
        saved = saved_ws_map.get(name)
        if saved:
            # Count saved windows with the same predicate as the live count in
            # the preceding block.
            def scnt(node: dict) -> int:
                """Count saved windows under a node."""
                if node.get("type") == "window":
                    return 1
                if node.get("type") in ("con", "floating_con") and node_app_id(node):
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
    """Perform the session restoration under the operation lock."""
    if not STATE_FILE.exists():
        log.info("No session file found.")
        return

    def _notify(msg: str, **kw) -> None:
        """Notify the user when notifications are enabled."""
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

        # Windows that failed on their own are collected here, so the
        # summary can report them without aborting the session.
        partial_failures.extend(ctx.failures)

        if hidden_scratchpad and detect_backend() != "i3":
            # Stage geometry on a scratch workspace before parking the windows
            # in the scratchpad. i3 rejects switching to internal workspaces,
            # so it stays on the restored workspace instead.
            cmd(_workspace_cmd(SCRATCH_RESTORE_WORKSPACE))
        if hidden_scratchpad:
            for node in hidden_scratchpad:
                try:
                    _restore_hidden_scratchpad(node, ctx)
                except Exception as exc:
                    partial_failures.append(f"hidden scratchpad: {exc}")
                    log.exception("Failed to restore hidden scratchpad window")

        restore_background_apps(
            background_apps,
            cache=ProcCache.snapshot() if background_apps else None,
            notify_user=notify_user,
        )
        cmd(_workspace_cmd(focused_workspace) if focused_workspace else "workspace 1")

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
    elif ctx.missing:
        _notify(
            f"{message} {len(ctx.missing)} window(s) did not come back. See logs.",
            urgency="normal",
        )
        log.warning("Windows not restored: %s", ", ".join(ctx.missing))
    else:
        _notify(f"{message} you can safely move now.")
    log.info("Restore complete.")
