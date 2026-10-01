#!/usr/bin/env python3

import re
import subprocess

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


def truncate(text: str) -> str:
    if len(text) > MAX_TEXT_LEN:
        return text[: MAX_TEXT_LEN - 3] + "..."
    return text


def main() -> None:
    print(truncate(rewrite(active_title())))


if __name__ == "__main__":
    main()
