#!/usr/bin/env python3
"""
Export the active Flint or Sand palette for chezmoi.

Palette definitions live in::

    palettes/flint/shared.yaml
    palettes/flint/dark.yaml
    palettes/flint/light.yaml

This script validates the definitions and exports the selected theme into
home/.chezmoidata.yaml, a generated file that chezmoi templates consume.

Usage::

    python scripts/build_palette_data.py --theme dark
    python scripts/build_palette_data.py --theme light
"""

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path

import flint_palette as lp
import yaml


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the active Flint palette for chezmoi."
    )
    parser.add_argument(
        "--theme",
        default="dark",
        help="Theme to export (dark | light). Default: dark.",
    )
    parser.add_argument(
        "--definitions-dir",
        type=Path,
        help="Palette definitions directory. Default: palettes/flint.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Output path. Default: .chezmoidata.yaml in the effective chezmoi "
            "source root. If .chezmoiroot exists, its value is respected."
        ),
    )
    return parser.parse_args(argv)


def to_plain_data(value: object) -> object:
    """
    Recursively convert generated palette data to YAML-safe built-in types.

    flint_palette uses OrderedDict internally to make output ordering
    explicit. PyYAML's general dumper can serialize those values with
    Python-specific object tags, so the generated data is normalized at the
    export boundary before being passed to safe_dump().
    """

    if isinstance(value, Mapping):
        return {to_plain_data(key): to_plain_data(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_plain_data(item) for item in value]

    return value


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    definitions_dir = args.definitions_dir or lp.default_definitions_dir(root)

    try:
        lp.check_all(definitions_dir)

        theme_names = lp.discover_themes(definitions_dir)
        if args.theme not in theme_names:
            lp.fail(
                f"unknown theme {args.theme}; available themes: "
                + ", ".join(theme_names)
            )

        data = lp.build_active_data(
            args.theme,
            definitions_dir,
            generated_by=f"scripts/build_palette_data.py --theme {args.theme}",
        )
        theme_name = data["flint"].get("meta", {}).get("name", args.theme.capitalize())
        serializable_data = to_plain_data(data)

        if args.output:
            output = args.output
            if output.is_dir():
                output = output / ".chezmoidata.yaml"
        else:
            source_root = lp.resolve_chezmoi_source_root(root)
            output = source_root / ".chezmoidata.yaml"

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            yaml.safe_dump(
                serializable_data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

        print(f"Exported {theme_name} theme '{args.theme}' to {output}")

    except lp.PaletteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
