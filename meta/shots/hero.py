#!/usr/bin/env python3
"""Capture or compose the split hero image."""

from __future__ import annotations

import argparse
import shlex
import time

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    HERO_SOCKET,
    HL_TEST,
    close_notifications,
    grim,
    kill_window,
    palette_mode,
    run,
    run_main,
    run_pillow,
    sway,
    sway_exec,
    wait_socket,
    wait_window,
)


def capture(mode: str) -> None:
    palette_mode(mode)
    sway("workspace", "3")
    HERO_SOCKET.unlink(missing_ok=True)
    try:
        sway_exec(
            [
                "kitty",
                "--class",
                "hero-nvim",
                "nvim",
                "--listen",
                str(HERO_SOCKET),
                "-c",
                "normal! zR",
                str(HL_TEST),
            ]
        )
        time.sleep(0.4)
        sway_exec(
            [
                "kitty",
                "--class",
                "hero-term",
                "sh",
                "-c",
                f"python3 {shlex.quote(str(HL_TEST))}; exec sh",
            ]
        )
        time.sleep(0.6)
        wait_window(app_id="hero-nvim")
        wait_window(app_id="hero-term")
        sway("[app_id=hero-nvim] focus")
        time.sleep(11)
        wait_socket(HERO_SOCKET)
        run(
            [
                "timeout",
                "5",
                "nvim",
                "--server",
                str(HERO_SOCKET),
                "--remote-send",
                "<Esc><CR>",
            ]
        )
        run(
            [
                "timeout",
                "8",
                "nvim",
                "--server",
                str(HERO_SOCKET),
                "--remote-expr",
                'execute("normal! gg330G0zz")',
            ]
        )
        time.sleep(0.8)
        close_notifications()
        grim(CAPTURES / f"stage-{mode}.png")
    finally:
        kill_window(app_id="hero-nvim")
        kill_window(app_id="hero-term")
        HERO_SOCKET.unlink(missing_ok=True)


def compose() -> None:
    run_pillow(
        "hero.py",
        str(CAPTURES / "stage-light.png"),
        str(CAPTURES / "stage-dark.png"),
        "-o",
        str(DOC_IMAGES / "hero.webp"),
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
