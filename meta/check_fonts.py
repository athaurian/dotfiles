#!/usr/bin/env python3
"""Check that the documentation site does not load fonts.

The shared theme supplies the fonts.
"""

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "zensical.toml"
THEME = REPO / "docs" / "stylesheets" / "extra.css"
FAMILIES = ("Geist", "Geist Mono")


def main():
    """Return 0 if font loading is off and the theme supplies the fonts."""
    site = tomllib.load(SITE.open("rb"))
    theme = site["project"]["theme"]
    css = THEME.read_text(encoding="utf-8")
    failures = []
    if theme.get("font") is not False:
        failures.append(f"{SITE.name}: font = {theme.get('font')!r}, expected false")
    for family in FAMILIES:
        if f'font-family: "{family}"' not in css:
            failures.append(f"{THEME.name}: missing {family} font face")
    for failure in failures:
        print(f"check-fonts: {failure}")
    if failures:
        return 1
    print(f"check-fonts: {SITE.name} loads fonts from the shared theme")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
