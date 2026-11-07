#!/usr/bin/env python3
"""Assert the docs site uses the font families from .chezmoidata.toml."""

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "home" / ".chezmoidata.toml"
SITE = REPO / "zensical.toml"


def main():
    """Return 0 when zensical.toml declares the configured fonts."""
    fonts = tomllib.load(FONTS.open("rb"))["fonts"]
    wanted = {"text": fonts["sans"], "code": fonts["code"]}
    theme = tomllib.load(SITE.open("rb"))["project"]["theme"]["font"]
    found = {role: theme.get(role) for role in wanted}
    failures = [
        f"{SITE.name}: font.{role} = {value!r}, expected {name!r}"
        for role, name in wanted.items()
        if (value := found[role]) != name
    ]
    for failure in failures:
        print(f"check-fonts: {failure}")
    if failures:
        return 1
    print(f"check-fonts: {SITE.name} uses {wanted['text']} and {wanted['code']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
