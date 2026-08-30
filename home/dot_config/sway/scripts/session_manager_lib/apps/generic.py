"""Generic app launcher and the central launch dispatcher."""

from __future__ import annotations

import logging
import shlex
import subprocess
import time
from pathlib import Path

from ..config import (
    APP_ID_COMMANDS,
    APP_PROFILES,
    DEFAULT_APP_PROFILE,
    WINDOW_SETTLE_POLL_INTERVAL,
)
from ..ipc import (
    WindowEventWatcher,
    get_tree,
    matches_app,
    matching_window_ids,
    walk_tree,
)
from ._common import reap_if_needed

log = logging.getLogger("session_manager")

__all__ = [
    "find_unclaimed_window",
    "get_cmd_from_app_id",
    "launch_and_get_id",
    "matching_window_ids",
    "wait_for_app_window",
    "wait_for_window_by_pid",
]


def get_cmd_from_app_id(app_id: str, class_name: str) -> list[str] | None:
    if app_id in ("foot", "foot_drop"):
        return None
    cmd = APP_ID_COMMANDS.get(app_id)
    if cmd:
        return shlex.split(cmd)
    desktop_id = app_id or class_name
    if desktop_id:
        for apps_dir in (
            Path.home() / ".local" / "share" / "applications",
            Path("/usr/share/applications"),
        ):
            if (apps_dir / f"{desktop_id}.desktop").exists():
                return ["gtk-launch", desktop_id]
    return []


def find_unclaimed_window(
    app_id: str,
    class_name: str,
    baseline_ids: set[int] | None = None,
    reject_floating: bool = False,
    claimed_ids: set[int] | None = None,
) -> int | None:
    baseline = baseline_ids or set()
    claimed = claimed_ids or set()
    for n in walk_tree(get_tree()):
        if n.get("type") not in ("con", "floating_con"):
            continue
        cid = n.get("id")
        if (
            cid is not None
            and matches_app(n, app_id, class_name)
            and cid not in claimed
            and cid not in baseline
            and not (reject_floating and n.get("type") == "floating_con")
        ):
            return cid
    return None


def _process_exited(process: object | None) -> bool:
    if process is None:
        return False
    poll = getattr(process, "poll", None)
    if not callable(poll):
        return False
    try:
        return poll() is not None
    except OSError:
        return True


def wait_for_app_window(
    app_id: str,
    class_name: str,
    watcher: WindowEventWatcher,
    *,
    settle: float = 0.3,
    reject_floating: bool = False,
    timeout: float = 20.0,
    baseline_ids: set[int] | None = None,
    claimed_ids: set[int] | None = None,
    process: object | None = None,
    fail_fast_on_exit: bool = False,
) -> int | None:
    baseline = baseline_ids or set()
    claimed = claimed_ids or set()
    deadline = time.monotonic() + timeout
    candidates: dict[int, dict] = {}

    while True:
        now = time.monotonic()
        if now >= deadline:
            break

        ready = sorted(
            (info["t"], cid)
            for cid, info in candidates.items()
            if (now - info["t"]) >= settle
            and not (reject_floating and info["floating"])
        )
        if ready:
            return ready[0][1]

        if fail_fast_on_exit and not candidates and _process_exited(process):
            break

        ev = watcher.get(
            timeout=min(WINDOW_SETTLE_POLL_INTERVAL, max(0.01, deadline - now))
        )
        if ev is None:
            continue

        cid = ev.container.get("id")
        if cid is None:
            continue

        if ev.change == "new":
            if cid in claimed or cid in baseline:
                continue
            if not matches_app(ev.container, app_id, class_name):
                continue
            candidates[cid] = {
                "t": ev.timestamp,
                "floating": ev.container.get("type") == "floating_con",
            }
        elif ev.change == "floating":
            if cid in candidates:
                candidates[cid]["floating"] = ev.container.get("type") == "floating_con"
        elif ev.change == "close":
            candidates.pop(cid, None)

    if candidates:
        tiled = sorted(
            (info["t"], cid) for cid, info in candidates.items() if not info["floating"]
        )
        if tiled:
            return tiled[0][1]
        if not reject_floating:
            return min((info["t"], cid) for cid, info in candidates.items())[1]

    return find_unclaimed_window(
        app_id,
        class_name,
        baseline_ids=baseline,
        reject_floating=reject_floating,
        claimed_ids=claimed,
    )


def wait_for_window_by_pid(
    watcher: WindowEventWatcher,
    pid: int,
    app_id: str,
    *,
    timeout: float = 15.0,
) -> int | None:
    """Event-driven replacement for the 150x get_tree() poll loops.

    Matches on pid, which is exact: no title/app_id ambiguity.
    Falls back to one tree scan if the event was missed.
    """
    deadline = time.monotonic() + timeout
    while True:
        now = time.monotonic()
        if now >= deadline:
            break
        ev = watcher.get(timeout=min(0.25, max(0.01, deadline - now)))
        if ev is None:
            continue
        if ev.change != "new":
            continue
        cont = ev.container
        if cont.get("pid") == pid and cont.get("id") is not None:
            return cont["id"]

    for n in walk_tree(get_tree()):
        if (
            n.get("type") in ("con", "floating_con")
            and n.get("pid") == pid
            and n.get("app_id") == app_id
            and n.get("id") is not None
        ):
            return n["id"]
    return None


def launch_and_get_id(node: dict, claimed_ids: set[int]) -> int | None:
    from .calibre import launch_ebook_viewer
    from .foot import launch_foot, launch_foot_drop
    from .mpv import launch_mpv
    from .thunar import launch_thunar
    from .zathura import launch_zathura

    app_id = node.get("app_id", "")
    class_name = node.get("class", "")

    if app_id == "helium":
        return None
    if app_id == "foot":
        return launch_foot(node, claimed_ids)
    if app_id == "foot_drop":
        return launch_foot_drop(node, claimed_ids)
    if app_id == "org.pwmt.zathura":
        return launch_zathura(node, claimed_ids)
    if app_id == "calibre-ebook-viewer":
        return launch_ebook_viewer(node, claimed_ids)
    if app_id == "thunar":
        return launch_thunar(node, claimed_ids)
    if app_id == "mpv":
        return launch_mpv(node, claimed_ids)

    cmd_args = get_cmd_from_app_id(app_id, class_name)
    if not cmd_args:
        return None

    profile = APP_PROFILES.get(app_id, DEFAULT_APP_PROFILE)
    baseline_ids = set(matching_window_ids(app_id, class_name))
    if profile.get("singleton") and baseline_ids:
        log.info("Skipping %s: instance already exists", app_id)
        return None

    win_id = None
    proc = None
    with WindowEventWatcher() as watcher:
        proc = subprocess.Popen(
            cmd_args,
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
                fail_fast_on_exit=app_id in APP_ID_COMMANDS,
            )
        finally:
            reap_if_needed(proc)

    if win_id:
        claimed_ids.add(win_id)
    return win_id
