#!/usr/bin/env python3
"""Capture or crop the status-bar figures."""

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
    kill_window,
    magick,
    mode_suffix,
    palette_mode,
    run_main,
    sway,
    sway_exec,
    wait_window,
)


def crop(mode: str) -> None:
    magick(
        str(CAPTURES / f"bar-{mode}.png"),
        "-quality",
        "92",
        str(DOC_IMAGES / f"bar{mode_suffix(mode)}.webp"),
    )


def capture(mode: str) -> None:
    try:
        palette_mode(mode)
        sway("workspace", "3")
        sway_exec(
            [
                "kitty",
                "--class",
                "bar-preview",
                "--title",
                "hl_test.py",
                "nvim",
                str(HL_TEST),
            ]
        )
        wait_window(app_id="bar-preview")
        time.sleep(10)
        sway("[app_id=bar-preview] focus")
        close_notifications()
        grim(CAPTURES / f"bar-{mode}.png", "-g", "0,0 1920x24")
    finally:
        kill_window(app_id="bar-preview")
    crop(mode)


def main() -> None:
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
