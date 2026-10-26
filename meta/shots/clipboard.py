#!/usr/bin/env python3
"""Capture or crop the clipboard-history picker figure."""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

from shotlib import (
    CAPTURES,
    CLIP_DB,
    CLIP_DIR,
    DOC_IMAGES,
    close_notifications,
    crop_round,
    error,
    grim,
    kill_window,
    mode_background,
    mode_edge,
    mode_suffix,
    palette_mode,
    run,
    run_main,
    sway,
    sway_exec,
    wait_window,
    window_geom_by_title,
    write_geom,
)

PICKER = Path.home() / ".local/bin/clipboard"
PREVIEW_IMAGE = Path(__file__).with_name("clipboard-preview.webp")


def seed() -> None:
    if not PREVIEW_IMAGE.exists():
        error(f"missing {PREVIEW_IMAGE}")
    shutil.rmtree(CLIP_DIR, ignore_errors=True)
    CLIP_DIR.mkdir(parents=True)
    entries = [
        b"git rebase -i HEAD~3\n",
        b'grep -rn "objects | select" home/ --include="*.sh"\n',
        b"https://github.com/athaurian/dotfiles\n",
        b"The palette lives in meta/palette.toml and every colour comes from it.\n",
    ]
    for entry in entries:
        run(
            ["cliphist", "-db-path", str(CLIP_DB), "store"],
            input=entry,
        )
    image = run(
        [
            "magick",
            str(PREVIEW_IMAGE),
            "-resize",
            "800x",
            "png:-",
        ],
        capture=True,
    ).stdout
    run(
        ["cliphist", "-db-path", str(CLIP_DB), "store"],
        input=image,
    )
    listing = run(
        ["cliphist", "-db-path", str(CLIP_DB), "list"],
        capture=True,
    ).stdout.splitlines()
    if not listing:
        error("cliphist did not store the mock history")
    latest_id = listing[0].split(b"\t", 1)[0]
    stored = run(
        ["cliphist", "-db-path", str(CLIP_DB), "decode", latest_id],
        capture=True,
    ).stdout
    if stored != image:
        error("cliphist did not round-trip the preview image")


def crop(mode: str) -> None:
    suffix = mode_suffix(mode)
    crop_round(
        CAPTURES / f"picker-clipboard{suffix}.png",
        DOC_IMAGES / f"picker-clipboard{suffix}.webp",
        crop="1428x728+246+188",
        radius=5,
        edge=mode_edge(mode),
        background=mode_background(mode),
    )


def capture(mode: str) -> None:
    if not PICKER.exists():
        error(f"missing {PICKER}")
    seed()
    palette_mode(mode)
    sway("workspace", "3")
    try:
        close_notifications()
        sway_exec([str(PICKER), "--db-path", str(CLIP_DB)])
        wait_window(title="clipboard_term", timeout=10)
        sway(
            "[con_mark=clipboard_term] scratchpad show, "
            "resize set width 75 ppt height 70 ppt, move position center"
        )
        time.sleep(0.5)
        sway("[con_mark=clipboard_term] focus")
        time.sleep(4)
        close_notifications()
        time.sleep(0.2)
        grim(CAPTURES / f"picker-clipboard{mode_suffix(mode)}.png")
        write_geom(
            CAPTURES / f"picker-clipboard{mode_suffix(mode)}.geom",
            window_geom_by_title("clipboard_term"),
        )
    finally:
        kill_window(title="clipboard_term")
        shutil.rmtree(CLIP_DIR, ignore_errors=True)
    crop(mode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("light", "dark", "seed", "crop"))
    parser.add_argument("mode", nargs="?", choices=("light", "dark"))
    args = parser.parse_args()
    if args.action in ("light", "dark"):
        if args.mode is not None:
            error(f"{args.action} does not take a mode")
        capture(args.action)
        return
    if args.action == "seed":
        if args.mode is not None:
            error("seed does not take a mode")
        seed()
        return
    if args.mode is None:
        error("crop requires light or dark")
    crop(args.mode)


if __name__ == "__main__":
    run_main(main)
