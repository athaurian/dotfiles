#!/usr/bin/env python3
"""Split hero image capture and composition."""

from __future__ import annotations

import argparse
import shlex
import time
import tomllib
from pathlib import Path

from shotlib import (
    CAPTURES,
    DOC_IMAGES,
    HERO_SOCKET,
    HL_TEST,
    ROOT,
    close_notifications,
    error,
    grim,
    kill_window,
    magick,
    mode_suffix,
    nvim_remote_send,
    palette_mode,
    prime_editor,
    run,
    run_main,
    run_pillow,
    sway,
    sway_exec,
    wait_socket,
    wait_window,
)

DIM = tomllib.loads((ROOT / "meta" / "palette.toml").read_text())["utility"]["dim"][
    "value"
]


def capture(mode: str) -> None:
    """Capture the editor and terminal stage in a mode."""
    launcher = Path.home() / ".local/bin/launcher_dim"
    if not launcher.exists():
        error(f"missing {launcher}")
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
        nvim_remote_send(HERO_SOCKET, "<Esc><CR>")
        prime_editor(HERO_SOCKET, line=330, column=12)
        time.sleep(0.8)
        close_notifications()
        grim(CAPTURES / f"stage-{mode}.png")
        sway_exec([str(launcher), DIM, "fuzzel"])
        time.sleep(1.5)
        close_notifications()
        grim(CAPTURES / f"stage-launcher-{mode}.png")
        magick(
            str(CAPTURES / f"stage-launcher-{mode}.png"),
            "-quality",
            "92",
            str(DOC_IMAGES / f"picker-dim{mode_suffix(mode)}.webp"),
        )
    finally:
        run(["pkill", "-x", "fuzzel"], check=False)
        kill_window(app_id="hero-nvim")
        kill_window(app_id="hero-term")
        HERO_SOCKET.unlink(missing_ok=True)


def compose() -> None:
    """Compose the split hero image from both stages."""
    run_pillow(
        "hero.py",
        str(CAPTURES / "stage-light.png"),
        str(CAPTURES / "stage-dark.png"),
        "-o",
        str(DOC_IMAGES / "hero.webp"),
    )


def main() -> None:
    """Run the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "compose"))
    args = parser.parse_args()
    if args.action == "compose":
        compose()
    else:
        capture(args.action)


if __name__ == "__main__":
    run_main(main)
