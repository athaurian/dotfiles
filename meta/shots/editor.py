#!/usr/bin/env python3
"""Capture or crop the Neovim editor figures."""

from __future__ import annotations

import argparse
import time

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    close_notifications,
    crop_round,
    error,
    find_window,
    grim,
    mode_background,
    mode_edge,
    mode_suffix,
    palette_mode,
    run_main,
    sway,
    write_geom,
)


def capture(mode: str) -> None:
    palette_mode(mode)
    sway("workspace", "3")
    window = find_window(app_id="editor-nvim")
    if window is None:
        error("open nvim in a window with app_id editor-nvim")
    sway("[app_id=editor-nvim] focus")
    close_notifications()
    time.sleep(0.3)
    grim(CAPTURES / f"editor-{mode}.png")
    rect = window["rect"]
    write_geom(
        CAPTURES / f"editor-{mode}.geom",
        f"{rect['width']}x{rect['height']}+{rect['x']}+{rect['y']}",
    )


def compose() -> None:
    for mode in ("dark", "light"):
        geom_path = CAPTURES / f"editor-{mode}.geom"
        if not geom_path.exists():
            error(f"missing {geom_path.relative_to(CAPTURES.parent.parent)}")
        crop_round(
            CAPTURES / f"editor-{mode}.png",
            DOC_IMAGES / f"neovim-editor{mode_suffix(mode)}.webp",
            crop=geom_path.read_text(encoding="utf-8").strip(),
            radius=5,
            edge=mode_edge(mode),
            background=mode_background(mode),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "compose"))
    args = parser.parse_args()
    if args.action == "compose":
        compose()
    else:
        capture(args.action)


if __name__ == "__main__":
    run_main(main)
