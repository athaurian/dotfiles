"""
Provides shared Flint palette loading, validation, and derivation logic.

Used by scripts/build_palette_data.py, reading palette definitions from::

    palettes/flint/shared.yaml
    palettes/flint/dark.yaml
    palettes/flint/light.yaml

Structural checks cover raw token existence and cross-theme role
parity. The pinned selection wash carries one blend-aware check: the
raw token must equal its source blend.
"""

from collections import OrderedDict
from pathlib import Path
from typing import NoReturn

import yaml


class PaletteError(Exception):
    pass


def fail(message: str) -> NoReturn:
    raise PaletteError(message)


SCHEMA_VERSION = 8

BACKGROUND_TOKEN = "background_primary"


def hex_to_bare(value: str) -> str:
    if not isinstance(value, str):
        fail(f"invalid hex color: {value!r}")
    return value.lower().lstrip("#")


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    bare = hex_to_bare(value)
    if len(bare) != 6:
        fail(f"invalid hex color: {value}")

    try:
        r = int(bare[0:2], 16)
        g = int(bare[2:4], 16)
        b = int(bare[4:6], 16)
    except ValueError:
        fail(f"invalid hex color: {value}")

    return r, g, b


def resolve_alias_target(
    theme_name: str,
    kind: str,
    alias: str,
    target: str,
    raw: dict,
    semantic: dict,
) -> str:
    if not isinstance(target, str) or not target:
        fail(f"{theme_name}: {kind} alias {alias} must name a role or raw token")

    visited = set()
    current = target

    while current in semantic:
        if current in visited:
            fail(f"{theme_name}: cyclical alias detected for {alias} -> {current}")
        visited.add(current)
        next_target = semantic[current]
        if next_target == current:
            break
        current = next_target

    if current in raw:
        return current

    fail(
        f"{theme_name}: {kind} alias {alias} references unknown semantic role "
        f"or raw token {target}"
    )


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing file: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"failed to read {path}: {exc}")

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"invalid YAML in {path}: {exc}")


def default_definitions_dir(root: Path) -> Path:
    return Path(root) / "palettes" / "flint"


def discover_themes(definitions_dir: Path) -> list[str]:
    definitions_dir = Path(definitions_dir)
    if not definitions_dir.is_dir():
        fail(f"palette definitions directory not found: {definitions_dir}")

    themes = sorted(
        path.stem for path in definitions_dir.glob("*.yaml") if path.stem != "shared"
    )

    if not themes:
        fail(f"no theme definitions found in {definitions_dir}")

    return themes


def load_shared(definitions_dir: Path) -> dict:
    path = Path(definitions_dir) / "shared.yaml"
    return load_yaml(path)


def load_theme(definitions_dir: Path, theme_name: str) -> dict:
    path = Path(definitions_dir) / f"{theme_name}.yaml"
    return load_yaml(path)


def effective_semantic(
    shared: dict, theme: dict, theme_name: str
) -> OrderedDict[str, str]:
    semantic = shared.get("semantic")
    if not isinstance(semantic, dict) or not semantic:
        fail(f"{theme_name}: shared palette definition is missing semantic roles")

    raw = theme.get("raw", {})
    result = OrderedDict(semantic.items())

    # Flatten app-scoped roles: apps.<app>.<key> -> role <app>_<key>.
    apps = shared.get("apps")
    if apps is not None:
        if not isinstance(apps, dict) or not apps:
            fail(f"{theme_name}: apps must be a non-empty object when present")
        for app_name, roles in apps.items():
            if not isinstance(roles, dict) or not roles:
                fail(f"{theme_name}: apps.{app_name} must be a non-empty object")
            for key, token in roles.items():
                if not isinstance(key, str) or not isinstance(token, str):
                    fail(f"{theme_name}: apps.{app_name} must map role names to tokens")
                role = f"{app_name}_{key}"
                if role in result:
                    fail(
                        f"{theme_name}: apps.{app_name}.{key} collides with role {role}"
                    )
                result[role] = token

    overrides = theme.get("semantic_overrides", {})
    if not isinstance(overrides, dict):
        fail(f"{theme_name}: semantic_overrides must be an object")

    for role, token in overrides.items():
        if role not in result:
            fail(f"{theme_name}: semantic override references unknown role {role}")
        if token == result[role]:
            fail(
                f"{theme_name}: semantic override {role}: {token} duplicates "
                f"the shared value and is redundant"
            )
        result[role] = token

    # Qt bevel ladder: 5 tokens mapping to the QPalette roles in
    # listed order (Light, Midlight, Button, Mid, Dark).
    bevel = theme.get("qt_bevel")
    if bevel is not None:
        if not isinstance(bevel, list) or len(bevel) != 5:
            fail(f"{theme_name}: qt_bevel must be a list of exactly 5 raw tokens")
        bevel_roles = ["qt_light", "qt_midlight", "qt_button", "qt_mid", "qt_dark"]
        for token, role in zip(bevel, bevel_roles):
            if not isinstance(token, str) or token not in raw:
                fail(f"{theme_name}: qt_bevel references unknown raw token {token}")
            result[role] = token

    final_result = OrderedDict()
    for role, target in result.items():
        resolved = resolve_alias_target(
            theme_name, "Semantic", role, target, raw, result
        )
        final_result[role] = resolved

    return final_result


def validate_meta(theme_name: str, theme: dict) -> None:
    meta = theme.get("meta")
    if not isinstance(meta, dict) or not meta:
        fail(f"{theme_name}: missing meta block")

    for key in ("name", "description", "variant"):
        value = meta.get(key)
        if not isinstance(value, str) or not value:
            fail(f"{theme_name}: meta.{key} must be a non-empty string")

    valid_variants = {"dark", "light"}
    if meta["variant"] not in valid_variants:
        fail(f"{theme_name}: meta.variant must be one of {sorted(valid_variants)}")


# The selection wash is the selection color flattened over the Qt Base
# backing at Obsidian's --text-selection color-mix percentages: 33% in
# .theme-dark, 20% on body. Every selection-wash consumer (Qt item
# selections, terminal and editor selections) shares this one pinned
# value so rows and single-coat surfaces render identically. The
# bytes pin those percentages: 0x54 = round(0.33 * 255),
# 0x33 = round(0.20 * 255). The validator pins the raw token to the
# blend, so the value cannot drift from the tokens it derives from.
SELECTION_WASH_ALPHA_BYTE = {"dark": 0x54, "light": 0x33}


def blend_over(
    rgb_fg: tuple[int, int, int], alpha: float, rgb_bg: tuple[int, int, int]
) -> tuple[int, int, int]:
    return tuple(
        round(alpha * fg + (1.0 - alpha) * bg) for fg, bg in zip(rgb_fg, rgb_bg)
    )


def validate_selection_wash(
    theme_name: str, variant: str, raw: dict, semantic: OrderedDict[str, str]
) -> list[str]:
    """Pins the selection wash to the blend it derives from.

    Requires the raw selection_wash token to equal the selection token
    blended at SELECTION_WASH_ALPHA_BYTE over the Qt Base backing, so
    the pinned value cannot drift from its inputs.
    """
    if variant not in SELECTION_WASH_ALPHA_BYTE:
        return [
            (
                f"{theme_name} has unknown variant {variant!r} "
                "for the selection wash check"
            )
        ]

    for token in ("selection", "selection_wash"):
        if token not in raw:
            return [
                (
                    f"{theme_name} is missing raw token {token} "
                    "for the selection wash check"
                )
            ]

    if "qt_base" not in semantic:
        return [
            (f"{theme_name} has no semantic role qt_base for the selection wash check")
        ]

    base_token = semantic["qt_base"]
    if base_token not in raw:
        return [
            (
                f"{theme_name} is missing raw token {base_token} "
                "for the selection wash check"
            )
        ]

    alpha = SELECTION_WASH_ALPHA_BYTE[variant] / 255.0
    baked = blend_over(hex_to_rgb(raw["selection"]), alpha, hex_to_rgb(raw[base_token]))
    expected = f"{baked[0]:02x}{baked[1]:02x}{baked[2]:02x}"
    actual = hex_to_bare(raw["selection_wash"])

    if actual != expected:
        return [
            (
                f"{theme_name} selection_wash is #{actual}, expected "
                f"#{expected} (selection at {SELECTION_WASH_ALPHA_BYTE[variant]:#04x} "
                f"over {base_token}); update the raw token to the blend"
            )
        ]

    return []


def validate_theme(
    theme_name: str,
    shared: dict,
    theme: dict,
    expected_raw_keys: set[str] | None = None,
) -> None:
    raw = theme.get("raw")
    if not isinstance(raw, dict) or not raw:
        fail(f"{theme_name}: missing raw palette")

    for token, value in raw.items():
        hex_to_rgb(value)

    if BACKGROUND_TOKEN not in raw:
        fail(f"{theme_name}: raw palette must include {BACKGROUND_TOKEN}")

    if expected_raw_keys is not None:
        actual_raw_keys = set(raw.keys())
        if actual_raw_keys != expected_raw_keys:
            missing = sorted(expected_raw_keys - actual_raw_keys)
            extra = sorted(actual_raw_keys - expected_raw_keys)
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extra:
                details.append("extra " + ", ".join(extra))
            fail(f"{theme_name}: raw token mismatch: " + "; ".join(details))

    validate_meta(theme_name, theme)
    semantic = effective_semantic(shared, theme, theme_name)

    for role, token in semantic.items():
        if token not in raw:
            fail(
                f"{theme_name}: semantic role {role} references "
                f"unknown raw token {token}"
            )

    ansi = shared.get("ansi")
    if not isinstance(ansi, dict) or not ansi:
        fail(f"{theme_name}: shared palette definition is missing ansi")

    for ansi_name, token in ansi.items():
        if token not in raw:
            fail(
                f"{theme_name}: ANSI color {ansi_name} references "
                f"unknown raw token {token}"
            )

    catppuccin = shared.get("catppuccin")
    if not isinstance(catppuccin, dict) or not catppuccin:
        fail(f"{theme_name}: shared palette definition is missing catppuccin")

    for alias, target in catppuccin.items():
        resolve_alias_target(
            theme_name,
            "Catppuccin",
            alias,
            target,
            raw,
            semantic,
        )

    alpha = shared.get("alpha")
    if not isinstance(alpha, dict):
        fail(f"{theme_name}: shared palette definition is missing alpha")

    for token, spec in alpha.items():
        if not isinstance(spec, list) or len(spec) != 2:
            fail(f"{theme_name}: alpha token {token} must be [base_token, alpha]")

        base_token, alpha_value = spec
        resolve_alias_target(
            theme_name,
            "Alpha",
            token,
            base_token,
            raw,
            semantic,
        )

        if isinstance(alpha_value, bool) or not isinstance(alpha_value, (int, float)):
            fail(f"{theme_name}: alpha token {token} has invalid alpha type")

        if not 0.0 <= float(alpha_value) <= 1.0:
            fail(f"{theme_name}: alpha token {token} has invalid alpha {alpha_value}")

    variant = theme.get("meta", {}).get("variant", theme_name)
    wash_errors = validate_selection_wash(theme_name, variant, raw, semantic)

    if wash_errors:
        fail(
            f"{theme_name} has {len(wash_errors)} validation issue(s):\n  - "
            + "\n  - ".join(wash_errors)
        )


def derive_raw(token: str, value: str) -> OrderedDict[str, object]:
    bare = hex_to_bare(value)
    r, g, b = hex_to_rgb(value)

    return OrderedDict(
        [
            ("token", token),
            ("hex", f"#{bare}"),
            ("bare", bare),
            ("triple", f"{r} {g} {b}"),
            ("bare_ff", f"{bare}ff"),
        ]
    )


def derive_alpha(
    token: str,
    base_token: str,
    alpha_value: float,
    raw_derived: OrderedDict[str, OrderedDict[str, object]],
) -> OrderedDict[str, object]:
    if base_token not in raw_derived:
        fail(f"alpha token {token} references unknown raw token {base_token}")

    alpha = float(alpha_value)
    if not 0.0 <= alpha <= 1.0:
        fail(f"alpha token {token} has invalid alpha {alpha}")

    base = raw_derived[base_token]

    bare = base["bare"]
    r = int(bare[0:2], 16)
    g = int(bare[2:4], 16)
    b = int(bare[4:6], 16)

    alpha_int = round(alpha * 255)
    alpha_hex = f"{alpha_int:02x}"
    bare8 = f"{base['bare']}{alpha_hex}"

    return OrderedDict(
        [
            ("token", token),
            ("base", base_token),
            ("alpha", alpha),
            ("hex", f"#{bare8}"),
            ("bare", bare8),
            ("triple", f"{r} {g} {b}"),
            ("rgba", f"rgba({r}, {g}, {b}, {alpha:g})"),
        ]
    )


def derive_theme(
    shared: dict, theme: dict, theme_name: str
) -> OrderedDict[str, object]:
    raw = theme.get("raw")
    if not isinstance(raw, dict) or not raw:
        fail(f"{theme_name}: missing raw palette")

    semantic = effective_semantic(shared, theme, theme_name)

    raw_derived = OrderedDict()
    for token, value in raw.items():
        raw_derived[token] = derive_raw(token, value)

    alpha = shared.get("alpha")
    if not isinstance(alpha, dict):
        fail(f"{theme_name}: shared palette definition is missing alpha")

    alpha_derived = OrderedDict()
    for token, spec in alpha.items():
        base_token, alpha_value = spec
        resolved_token = resolve_alias_target(
            theme_name,
            "Alpha",
            token,
            base_token,
            raw,
            semantic,
        )
        alpha_derived[token] = derive_alpha(
            token,
            resolved_token,
            alpha_value,
            raw_derived,
        )

    resolved = OrderedDict()
    for role, token in semantic.items():
        resolved[role] = raw_derived[token]

    ansi = shared.get("ansi", {})
    ansi_resolved = OrderedDict()
    for ansi_name, token in ansi.items():
        ansi_resolved[ansi_name] = raw_derived[token]

    catppuccin = shared.get("catppuccin", {})
    catppuccin_resolved = OrderedDict()
    for alias, target in catppuccin.items():
        token = resolve_alias_target(
            theme_name,
            "Catppuccin",
            alias,
            target,
            raw,
            semantic,
        )
        catppuccin_resolved[alias] = raw_derived[token]

    lut_palette = shared.get("lut_palette", {})
    lut_resolved = OrderedDict()
    if isinstance(lut_palette, dict):
        for variant, tokens in lut_palette.items():
            entries = []
            for token in tokens:
                resolved_token = resolve_alias_target(
                    theme_name,
                    "LUT",
                    f"{variant}[]",
                    token,
                    raw,
                    semantic,
                )
                entries.append(raw_derived[resolved_token])
            lut_resolved[variant] = entries

    return OrderedDict(
        [
            ("meta", theme.get("meta", {})),
            ("catppuccin_flavor", theme.get("catppuccin_flavor", theme_name)),
            ("raw", raw_derived),
            ("alpha", alpha_derived),
            ("semantic", semantic),
            ("resolved", resolved),
            ("ansi", ansi),
            ("ansi_resolved", ansi_resolved),
            ("catppuccin", catppuccin),
            ("catppuccin_resolved", catppuccin_resolved),
            ("lut_palette", lut_palette),
            ("lut_resolved", lut_resolved),
            ("appearance", theme.get("appearance", {})),
            ("desktop", shared.get("desktop", {})),
        ]
    )


def build_active_data(
    theme_name: str,
    definitions_dir: Path,
    generated_by: str = "flint_palette",
) -> OrderedDict[str, object]:
    """Exports every theme plus active-theme aliases for templates.

    Top-level sections alias the active theme. Each theme also gets a
    named block (``flint.dark``, ...) for apps that render both
    palettes from one file, like the foot terminal.

    Args:
        theme_name: Active theme to alias at the top level.
        definitions_dir: Directory holding the palette definitions.
        generated_by: Label recorded in the generated output.

    Returns:
        Ordered mapping with the ``flint`` block for templates.
    """
    definitions_dir = Path(definitions_dir)
    theme_names = discover_themes(definitions_dir)

    if theme_name not in theme_names:
        fail(f"unknown theme {theme_name}; available themes: " + ", ".join(theme_names))

    shared = load_shared(definitions_dir)
    derived = OrderedDict()
    for name in theme_names:
        theme = load_theme(definitions_dir, name)
        validate_theme(name, shared, theme, None)
        derived[name] = derive_theme(shared, theme, name)

    active = derived[theme_name]

    theme_blocks = OrderedDict()
    for name in theme_names:
        data = derived[name]
        theme_blocks[name] = OrderedDict(
            [
                ("meta", data["meta"]),
                ("catppuccin_flavor", data["catppuccin_flavor"]),
                ("appearance", data["appearance"]),
                ("raw", data["raw"]),
                ("alpha", data["alpha"]),
                ("semantic", data["semantic"]),
                ("resolved", data["resolved"]),
                ("ansi_resolved", data["ansi_resolved"]),
                ("catppuccin_resolved", data["catppuccin_resolved"]),
                ("lut_resolved", data["lut_resolved"]),
            ]
        )

    flint = OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("generated_by", generated_by),
            ("active_theme", theme_name),
            ("available_themes", theme_names),
            ("desktop", shared.get("desktop", {})),
            ("ansi", shared.get("ansi", {})),
            ("catppuccin", shared.get("catppuccin", {})),
            ("lut_palette", shared.get("lut_palette", {})),
            # Active-theme aliases for .flint.resolved consumers
            ("meta", active["meta"]),
            ("catppuccin_flavor", active["catppuccin_flavor"]),
            ("appearance", active["appearance"]),
            ("raw", active["raw"]),
            ("alpha", active["alpha"]),
            ("semantic", active["semantic"]),
            ("resolved", active["resolved"]),
            ("ansi_resolved", active["ansi_resolved"]),
            ("catppuccin_resolved", active["catppuccin_resolved"]),
            ("lut_resolved", active["lut_resolved"]),
        ]
    )
    flint.update(theme_blocks)

    return OrderedDict([("flint", flint)])


def check_all(definitions_dir: Path) -> list[str]:
    definitions_dir = Path(definitions_dir)
    theme_names = discover_themes(definitions_dir)
    shared = load_shared(definitions_dir)

    expected_raw_keys = None
    role_sets: dict[str, set[str]] = {}

    for theme_name in theme_names:
        theme = load_theme(definitions_dir, theme_name)
        raw_section = theme.get("raw", {})

        if expected_raw_keys is None:
            if isinstance(raw_section, dict):
                expected_raw_keys = set(raw_section.keys())
            else:
                expected_raw_keys = set()

        validate_theme(theme_name, shared, theme, expected_raw_keys)
        role_sets[theme_name] = set(
            effective_semantic(shared, theme, theme_name).keys()
        )

    reference = theme_names[0]
    base_set = role_sets[reference]
    for theme_name in theme_names[1:]:
        current = role_sets[theme_name]
        missing = sorted(base_set - current)
        extra = sorted(current - base_set)
        if missing or extra:
            fail(
                f"role parity: {theme_name} diverges from {reference}: "
                f"missing {missing}, extra {extra}"
            )

    return []


def resolve_chezmoi_source_root(root: Path) -> Path:
    root = Path(root)
    marker = root / ".chezmoiroot"

    if not marker.is_file():
        return root

    try:
        text = marker.read_text(encoding="utf-8")
    except OSError:
        return root

    for line in text.splitlines():
        line = line.strip().strip('"').strip("'")
        if not line or line.startswith("#"):
            continue

        candidate = Path(line).expanduser()
        if candidate.is_absolute():
            return candidate

        return (root / candidate).resolve()

    return root
