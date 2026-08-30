"""Helium browser: group save/restore with title matching."""

from __future__ import annotations

import json
import logging
import subprocess
import time

from ..config import (
    APP_PROFILES,
    DEFAULT_APP_PROFILE,
    HELIUM_ASSIGNMENT_TIMEOUT,
    HELIUM_CONFIG_DIR,
    HELIUM_TITLE_GRACE_PERIOD,
    HELIUM_WINDOW_STALL_TIMEOUT,
    WINDOW_SETTLE_POLL_INTERVAL,
)
from ..ipc import WindowEventWatcher, get_tree, walk_tree
from ..proc_cache import ProcCache
from ..state import RestoreContext
from ._common import normalize_title, reap_if_needed

log = logging.getLogger("session_manager")


def _assign_by_title(
    remaining_saved: list[int],
    unassigned: list[int],
    titles: dict[int, str],
    ctx: RestoreContext,
) -> bool:
    """Match saved helium windows to live windows by title.

    Tries exact match first, then normalised (lowercased, collapsed
    whitespace).  Returns True if at least one new match was made.
    """
    matched_any = False
    for idx in list(remaining_saved):
        if ctx.helium_restored_ids[idx] is not None:
            remaining_saved.remove(idx)
            continue
        saved_title = ctx.helium_saved_nodes[idx].get("name", "").strip()
        if not saved_title:
            continue
        match = next(
            (cid for cid in unassigned if titles.get(cid) == saved_title),
            None,
        )
        if match is None:
            norm_saved = normalize_title(saved_title)
            match = next(
                (
                    cid
                    for cid in unassigned
                    if norm_saved and normalize_title(titles.get(cid, "")) == norm_saved
                ),
                None,
            )
        if match is not None:
            ctx.helium_restored_ids[idx] = match
            unassigned.remove(match)
            remaining_saved.remove(idx)
            matched_any = True
    return matched_any


def _matching_helium_ids() -> list[int]:
    return [
        n["id"]
        for n in walk_tree(get_tree())
        if n.get("type") in ("con", "floating_con")
        and n.get("app_id") == "helium"
        and n.get("id") is not None
    ]


def collect_helium_nodes(node: dict, ctx: RestoreContext) -> None:
    if node.get("type") == "window" and node.get("app_id") == "helium":
        idx = len(ctx.helium_saved_nodes)
        ctx.helium_saved_nodes.append(node)
        ctx.helium_saved_index[id(node)] = idx
        ctx.helium_restored_ids.append(None)
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        collect_helium_nodes(child, ctx)


def _suppress_helium_crash_prompt(cache: ProcCache | None = None) -> None:
    cache = cache or ProcCache.snapshot()
    if cache.process_named_running("helium"):
        log.info("Helium already running; skipping crash-marker patch.")
        return

    prefs_path = HELIUM_CONFIG_DIR / "Default" / "Preferences"
    if not prefs_path.exists():
        return
    try:
        data = json.loads(prefs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log.warning("Could not parse Helium Preferences")
        return

    profile = data.get("profile")
    if not isinstance(profile, dict):
        return

    changed = False
    if profile.get("exit_type") != "Normal":
        profile["exit_type"] = "Normal"
        changed = True
    if profile.get("exited_cleanly") is False:
        profile["exited_cleanly"] = True
        changed = True

    if changed:
        try:
            prefs_path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            log.warning("Could not rewrite Helium Preferences")


def _live_new_helium_windows(baseline_ids: set[int]) -> dict[int, str]:
    result: dict[int, str] = {}
    for n in walk_tree(get_tree()):
        cid = n.get("id")
        if (
            cid is not None
            and n.get("type") in ("con", "floating_con")
            and n.get("app_id") == "helium"
            and cid not in baseline_ids
        ):
            result[cid] = n.get("name") or ""
    return result


def _restore_helium_group(ctx: RestoreContext) -> None:
    if ctx.helium_restore_started:
        return
    ctx.helium_restore_started = True
    if not ctx.helium_saved_nodes:
        return

    count = len(ctx.helium_saved_nodes)
    profile = APP_PROFILES.get("helium", DEFAULT_APP_PROFILE)
    baseline_ids = set(_matching_helium_ids())
    _suppress_helium_crash_prompt()

    # If helium is already running and we already have enough windows,
    # reuse them directly without launching a new instance (which would just
    # signal the existing one and exit, but still cost time).
    if (
        ProcCache.snapshot().process_named_running("helium")
        and len(baseline_ids) >= count
    ):
        # Collect current titles for existing windows
        existing_windows: dict[int, str] = {}
        for n in walk_tree(get_tree()):
            cid = n.get("id")
            if (
                cid is not None
                and n.get("type") in ("con", "floating_con")
                and n.get("app_id") == "helium"
                and cid in baseline_ids
            ):
                existing_windows[cid] = n.get("name") or ""
                if len(existing_windows) >= count:
                    break
        if existing_windows:
            # Directly assign without launching
            remaining_saved = list(range(count))
            unassigned = list(existing_windows.keys())

            _assign_by_title(remaining_saved, unassigned, dict(existing_windows), ctx)
            for idx in list(remaining_saved):
                if ctx.helium_restored_ids[idx] is None and unassigned:
                    ctx.helium_restored_ids[idx] = unassigned.pop(0)
                elif ctx.helium_restored_ids[idx] is None:
                    break
            return

    with WindowEventWatcher() as watcher:
        proc = subprocess.Popen(
            ["helium-browser", "--restore-last-session"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        windows: dict[int, str] = {}
        deadline = time.monotonic() + profile["timeout"]
        next_tree_scan = time.monotonic() + 0.25
        last_new = time.monotonic()

        try:
            while len(windows) < count and time.monotonic() < deadline:
                # If the launcher exited quickly (helium already running and just
                # signaled the existing instance), don't burn the full 30s timeout
                # waiting for new windows that will never appear.
                if proc.poll() is not None:
                    before = len(windows)
                    windows.update(_live_new_helium_windows(baseline_ids))
                    if not windows:
                        break
                    if len(windows) > before:
                        last_new = time.monotonic()
                    # Have some windows but not all; give a short grace for titles
                    if deadline - time.monotonic() > HELIUM_TITLE_GRACE_PERIOD:
                        deadline = time.monotonic() + HELIUM_TITLE_GRACE_PERIOD
                # Stall detection: if we have some windows but no new one for a while, stop waiting
                if (
                    windows
                    and time.monotonic() - last_new > HELIUM_WINDOW_STALL_TIMEOUT
                ):
                    break
                now = time.monotonic()
                wait = min(
                    WINDOW_SETTLE_POLL_INTERVAL,
                    max(0.01, deadline - now),
                    max(0.01, next_tree_scan - now),
                )
                ev = watcher.get(timeout=wait)
                if ev is None:
                    pass
                else:
                    cont = ev.container
                    cid = cont.get("id")
                    if (
                        cid is not None
                        and cont.get("app_id") == "helium"
                        and cid not in baseline_ids
                    ):
                        if ev.change == "new" or (
                            ev.change == "title" and cid in windows
                        ):
                            is_new = cid not in windows
                            windows[cid] = cont.get("name") or ""
                            if is_new:
                                last_new = time.monotonic()
                        elif ev.change == "close":
                            windows.pop(cid, None)

                if len(windows) >= count:
                    break

                now = time.monotonic()
                if now >= next_tree_scan:
                    before = len(windows)
                    windows.update(_live_new_helium_windows(baseline_ids))
                    if len(windows) > before:
                        last_new = time.monotonic()
                    next_tree_scan = now + 0.25
        finally:
            reap_if_needed(proc)

        if len(windows) < count:
            windows.update(_live_new_helium_windows(baseline_ids))
            if len(windows) < count:
                missing = count - len(windows)
                log.info(
                    "Helium missing %d windows, launching via --new-window", missing
                )
                for idx in range(missing):
                    try:
                        p = subprocess.Popen(
                            ["helium-browser", "--new-window", "about:blank"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True,
                        )
                        time.sleep(0.6)
                        new_windows = _live_new_helium_windows(baseline_ids)
                        for cid, title in new_windows.items():
                            if cid not in windows:
                                windows[cid] = title
                        reap_if_needed(p)
                    except OSError:
                        log.warning("Failed to launch extra helium window")
                    if len(windows) >= count:
                        break
                windows.update(_live_new_helium_windows(baseline_ids))

        if not windows:
            log.warning("Helium started, but no new windows found.")
            return
        if len(windows) < count:
            log.warning("Helium restored only %d/%d windows.", len(windows), count)

        remaining_saved = list(range(count))
        unassigned = list(windows.keys())

        def _live_titles_for_unassigned() -> dict[int, str]:
            ids = set(unassigned)
            if not ids:
                return {}
            return {
                n["id"]: (n.get("name") or "")
                for n in walk_tree(get_tree())
                if n.get("type") in ("con", "floating_con")
                and n.get("app_id") == "helium"
                and n.get("id") in ids
            }

        def _match_remaining(titles: dict[int, str]) -> None:
            while _assign_by_title(remaining_saved, unassigned, titles, ctx):
                pass

        assignment_deadline = time.monotonic() + min(
            HELIUM_ASSIGNMENT_TIMEOUT, profile["timeout"]
        )
        _match_remaining(dict(windows))
        next_title_scan = time.monotonic() + 1.0
        while remaining_saved and unassigned and time.monotonic() < assignment_deadline:
            now = time.monotonic()
            wait = min(0.5, max(0.01, assignment_deadline - now))
            ev = watcher.get(timeout=wait)
            if ev is not None:
                cont = ev.container
                cid = cont.get("id")
                if (
                    cid is not None
                    and cont.get("app_id") == "helium"
                    and cid in unassigned
                ):
                    if ev.change == "title":
                        windows[cid] = cont.get("name") or ""
                        _match_remaining(dict(windows))
                    elif ev.change == "close":
                        windows.pop(cid, None)
                        unassigned.remove(cid)
                        _match_remaining(dict(windows))

            now = time.monotonic()
            if now >= next_title_scan:
                live_titles = _live_titles_for_unassigned()
                if live_titles:
                    windows.update(live_titles)
                    _match_remaining(dict(windows))
                next_title_scan = now + 1.0

        for idx in list(remaining_saved):
            if ctx.helium_restored_ids[idx] is None and unassigned:
                ctx.helium_restored_ids[idx] = unassigned.pop(0)
            elif ctx.helium_restored_ids[idx] is None:
                break


def get_helium_restored_id(node: dict, ctx: RestoreContext) -> int | None:
    if not ctx.helium_restore_started:
        _restore_helium_group(ctx)
    idx = ctx.helium_saved_index.get(id(node))
    if idx is None:
        return None
    return ctx.helium_restored_ids[idx]
