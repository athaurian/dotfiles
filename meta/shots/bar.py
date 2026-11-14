#!/usr/bin/env python3
"""Status-bar figure capture and cropping."""

from __future__ import annotations

import argparse
import time

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    HL_TEST,
    close_notifications,
    error,
    grim,
    magick,
    mode_suffix,
    palette_mode,
    run_main,
    spawn,
    stop,
    sway,
    wait_window,
)


def crop(mode: str) -> None:
    """Crop the status-bar capture for a mode."""
    magick(
        str(CAPTURES / f"bar-{mode}.png"),
        "-quality",
        "92",
        str(DOC_IMAGES / f"bar{mode_suffix(mode)}.webp"),
    )


def capture(mode: str) -> None:
    """Capture the status bar in a mode."""
    palette_mode(mode)
    sway("workspace", "3")
    process = spawn(["kitty", "--title", "hl_test.py", "nvim", str(HL_TEST)])
    try:
        wait_window(pid=process.pid)
        time.sleep(10)
        sway(f"[pid={process.pid}] focus")
        close_notifications()
        grim(CAPTURES / f"bar-{mode}.png", "-g", "0,0 1920x24")
    finally:
        stop(process)
    crop(mode)


def main() -> None:
    """Run the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "crop"))
    parser.add_argument("mode", nargs="?", choices=("light", "dark"))
    args = parser.parse_args()
    if args.action in ("light", "dark"):
        if args.mode is not None:
            error(f"{args.action} does not take a mode")
        capture(args.action)
        return
    if args.mode is None:
        error("crop requires light or dark")
    crop(args.mode)


if __name__ == "__main__":
    run_main(main)
