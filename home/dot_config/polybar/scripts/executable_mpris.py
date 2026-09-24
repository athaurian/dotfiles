#!/usr/bin/env python3
"""
Provides the polybar MPRIS module script.

Polls playerctl for the active player's metadata and emits plain text with
polybar format tags. polybar has no Waybar-style hide-empty-text, so an
empty line keeps the module collapsed when no player is active. Color tags
mute the label while paused and restore the bar foreground while playing.
"""

import subprocess

ICON_PLAYING = "󰐊"
ICON_PAUSED = "󰏤"
MAX_TEXT_LEN = 56
MUTED = "#8A8A8A"


def query(args: list[str]) -> str:
    try:
        out = subprocess.run(
            ["playerctl", *args], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def main() -> None:
    status = query(["status"])
    if status not in ("Playing", "Paused"):
        # No player, or a stopped player: nothing to show, the way waybar
        # hides the module once its grace window lapses.
        print()
        return
    artist = query(["metadata", "artist"])
    title = query(["metadata", "title"])
    if not artist and not title:
        # Metadata is briefly empty while a player starts up; waybar hides
        # the module then instead of flashing a placeholder.
        print()
        return
    if artist and title:
        text = f"{artist} - {title}"
    elif title:
        text = title
    else:
        text = artist
    if len(text) > MAX_TEXT_LEN:
        text = text[: MAX_TEXT_LEN - 1] + "…"
    icon = ICON_PLAYING if status == "Playing" else ICON_PAUSED
    if status == "Playing":
        print(f"{icon} {text}")
    else:
        print(f"%{{F#{MUTED}}}{icon} {text}%{{F-}}")


if __name__ == "__main__":
    main()
