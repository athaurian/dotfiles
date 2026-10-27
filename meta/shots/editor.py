#!/usr/bin/env python3
"""Capture or crop the Neovim editor figures."""

from __future__ import annotations

import argparse
import time

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    EDITOR_SOCKET,
    HL_TEST,
    close_notifications,
    crop_round,
    error,
    find_window,
    grim,
    kill_window,
    mode_background,
    mode_edge,
    mode_suffix,
    nvim_remote_send,
    palette_mode,
    prime_editor,
    run_main,
    sway,
    sway_exec,
    verify_editor,
    wait_socket,
    wait_window,
    write_geom,
)


def capture(mode: str) -> None:
    palette_mode(mode)
    sway("workspace", "3")
    kill_window(app_id="editor-nvim")
    EDITOR_SOCKET.unlink(missing_ok=True)
    try:
        sway_exec(
            [
                "kitty",
                "--class",
                "editor-nvim",
                "nvim",
                "--listen",
                str(EDITOR_SOCKET),
                "+330",
                str(HL_TEST),
            ]
        )
        wait_window(app_id="editor-nvim")
        wait_socket(EDITOR_SOCKET)
        time.sleep(11)
        for _ in range(3):
            nvim_remote_send(EDITOR_SOCKET, "<Esc><CR>")
            time.sleep(1)
        nvim_remote_send(EDITOR_SOCKET, ":lua Snacks.explorer()<CR>")
        time.sleep(1.5)
        nvim_remote_send(EDITOR_SOCKET, "I")
        time.sleep(1.5)
        prime_editor(EDITOR_SOCKET)
        verify_editor(EDITOR_SOCKET, path=HL_TEST)
        sway("[app_id=editor-nvim] focus")
        close_notifications()
        time.sleep(0.3)
        grim(CAPTURES / f"editor-{mode}.png")
        window = find_window(app_id="editor-nvim")
        if window is None:
            error("the editor window disappeared")
        rect = window["rect"]
        write_geom(
            CAPTURES / f"editor-{mode}.geom",
            f"{rect['width']}x{rect['height']}+{rect['x']}+{rect['y']}",
        )
    finally:
        kill_window(app_id="editor-nvim")
        EDITOR_SOCKET.unlink(missing_ok=True)


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
