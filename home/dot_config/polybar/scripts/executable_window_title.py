#!/usr/bin/env python3
"""
Prints the active window title with Waybar's sway/window rewrite rules.

polybar's internal/xwindow label only supports truncation tokens, so the
rewrite table lives in this script instead. The rules mirror
waybar/config.jsonc (sway/window); the 56-column cap is stricter than
waybar's 72 so long titles cannot push the right-hand modules off-screen.
Empty titles print as a single space so the module slot stays put, as in
Waybar.
"""

import re
import subprocess

MAX_TEXT_LEN = 56

# Waybar sway/window `rewrite` parity, applied in config order.
REWRITES = (
    (r"^$", " "),
    (r"(.*) - Helium", r"\1"),
    (r"^• Discord \| (.*)$", r"\1"),
    (r"^nvim (.*)$", r" Editing \1"),
)


def active_title() -> str:
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.removesuffix("\n")


def rewrite(title: str) -> str:
    for pattern, replacement in REWRITES:
        title = re.sub(pattern, replacement, title)
    return title


def truncate(text: str) -> str:
    if len(text) > MAX_TEXT_LEN:
        return text[: MAX_TEXT_LEN - 3] + "..."
    return text


def main() -> None:
    print(truncate(rewrite(active_title())))


if __name__ == "__main__":
    main()
