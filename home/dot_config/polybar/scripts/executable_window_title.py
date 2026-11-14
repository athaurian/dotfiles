#!/usr/bin/env python3

import re
import subprocess
import unicodedata

MAX_TEXT_LEN = 56

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


def char_width(ch: str) -> int:
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def truncate(text: str) -> str:
    if sum(char_width(ch) for ch in text) <= MAX_TEXT_LEN:
        return text
    width = 0
    for i, ch in enumerate(text):
        w = char_width(ch)
        if width + w > MAX_TEXT_LEN - 1:
            return text[:i] + "…"
        width += w
    return text


def main() -> None:
    print(truncate(rewrite(active_title())))


if __name__ == "__main__":
    main()
