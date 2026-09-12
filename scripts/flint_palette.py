"""
Provides shared Flint palette loading, validation, and derivation logic.

Used by scripts/build_palette_data.py, reading palette definitions from::

    palettes/flint/shared.yaml
    palettes/flint/dark.yaml
    palettes/flint/light.yaml

Validation covers selected WCAG 2.2 AA contrast pairs only: SC 1.4.3
Contrast (Minimum) and SC 1.4.11 Non-text Contrast for the listed rows.
No house-style checks. Passing rows are not a WCAG conformance claim.
"""

from collections import OrderedDict
from pathlib import Path
from typing import NoReturn

import yaml


class PaletteError(Exception):
    pass


def fail(message: str) -> NoReturn:
    raise PaletteError(message)


SCHEMA_VERSION = 7

BACKGROUND_TOKEN = "bg"


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


def srgb_channel_to_linear(channel: int) -> float:
    c = channel / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return (
        0.2126 * srgb_channel_to_linear(r)
        + 0.7152 * srgb_channel_to_linear(g)
        + 0.0722 * srgb_channel_to_linear(b)
    )


def contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    lum_a = relative_luminance(rgb_a)
    lum_b = relative_luminance(rgb_b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def role_rgb(raw: dict, semantic: dict, role: str) -> tuple[int, int, int]:
    if role not in semantic:
        fail(f"contrast check references unknown semantic role {role}")

    token = semantic[role]
    if token not in raw:
        fail(f"semantic role {role} references unknown raw token {token}")

    return hex_to_rgb(raw[token])


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

    # Apply variant overrides
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

    # Qt bevel ladder: 5 ramp tokens, lightest -> darkest.
    # Order is not a WCAG requirement; roles are derived in listed order.
    bevel = theme.get("qt_bevel")
    if bevel is not None:
        if not isinstance(bevel, list) or len(bevel) != 5:
            fail(f"{theme_name}: qt_bevel must be a list of exactly 5 raw tokens")
        bevel_roles = ["qt_light", "qt_midlight", "qt_button", "qt_mid", "qt_dark"]
        for token, role in zip(bevel, bevel_roles):
            if not isinstance(token, str) or token not in raw:
                fail(f"{theme_name}: qt_bevel references unknown raw token {token}")
            result[role] = token

    # Resolve all semantic aliases to concrete raw tokens
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


def load_contrast_checks(theme_name: str, shared: dict) -> list[tuple[str, str, float]]:
    checks = shared.get("contrast_checks")
    if not isinstance(checks, list) or not checks:
        fail(f"{theme_name}: shared palette definition is missing contrast_checks")

    result: list[tuple[str, str, float]] = []
    for row in checks:
        if not isinstance(row, list) or len(row) != 3:
            fail(f"{theme_name}: contrast_checks rows must be [fg_role, bg_role, min]")
        fg_role, bg_role, minimum = row
        if not isinstance(fg_role, str) or not isinstance(bg_role, str):
            fail(f"{theme_name}: contrast_checks rows must name roles as strings")
        if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
            fail(f"{theme_name}: contrast_checks row {row} has invalid minimum")
        if float(minimum) <= 0:
            fail(f"{theme_name}: contrast_checks row {row} has non-positive minimum")
        result.append((fg_role, bg_role, float(minimum)))
    return result


def validate_contrast(
    theme_name: str, raw: dict, semantic: dict, checks: list[tuple[str, str, float]]
) -> list[str]:
    seen = set()
    errors = []

    for fg_role, bg_role, minimum in checks:
        key = (fg_role, bg_role, minimum)
        if key in seen:
            continue
        seen.add(key)

        fg_rgb = role_rgb(raw, semantic, fg_role)
        bg_rgb = role_rgb(raw, semantic, bg_role)
        ratio = contrast_ratio(fg_rgb, bg_rgb)

        if ratio + 1e-9 < minimum:
            errors.append(
                f"{fg_role} on {bg_role} is {ratio:.2f}:1, "
                f"expected at least {minimum:.1f}:1"
            )

    return errors


def validate_ansi_relationships(
    theme_name: str, raw: dict, semantic: dict, ansi: dict
) -> list[str]:
    """Enforces WCAG 2.2 AA SC 1.4.3 for terminal text.

    Every ANSI color used as body text needs 4.5:1 on the terminal
    background. Surfaces are not terminal backgrounds, so no
    ANSI-on-surface floor exists.
    """
    base_rgb = hex_to_rgb(raw[BACKGROUND_TOKEN])
    base_lum = relative_luminance(base_rgb)
    is_light = base_lum > 0.5
    errors = []

    # In light mode, black and chromatic colors are foreground text;
    # white/bright_white are light background/badges
    # In dark mode, white and chromatic colors are foreground text;
    # black/bright_black are dark backgrounds
    excluded_from_text = (
        ("white", "bright_white") if is_light else ("black", "bright_black")
    )

    text_ansi_tokens = {
        name: token for name, token in ansi.items() if name not in excluded_from_text
    }

    for ansi_name, token in text_ansi_tokens.items():
        ansi_rgb = hex_to_rgb(raw[token])
        ratio = contrast_ratio(ansi_rgb, base_rgb)

        if ratio + 1e-9 < 4.5:
            errors.append(
                f"ANSI {ansi_name} on background is {ratio:.2f}:1, "
                "expected at least 4.5:1"
            )

    # Note: ANSI colors are terminal body text on the terminal
    # background only. Surfaces are panels and popups, not terminal
    # backgrounds, so WCAG AA sets no ANSI-on-surface floor. If a
    # future template renders ANSI body text on a surface, add an
    # explicit 4.5 check for that pair instead of a blanket rule.

    return errors


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

    contrast_checks = load_contrast_checks(theme_name, shared)

    # Selected WCAG 2.2 AA pairs only: SC 1.4.3 normal text and SC 1.4.11
    # graphics for the listed rows. Not a conformance claim.
    contrast_errors = validate_contrast(theme_name, raw, semantic, contrast_checks)
    ansi_errors = validate_ansi_relationships(theme_name, raw, semantic, ansi)

    all_errors = contrast_errors + ansi_errors
    if all_errors:
        fail(
            f"{theme_name} has {len(all_errors)} validation issue(s):\n  - "
            + "\n  - ".join(all_errors)
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

    The top-level sections (``resolved``, ``alpha``, ...) alias the
    active theme's data so existing templates keep working unchanged.
    Each theme also gets a named block (``flint.dark``,
    ``flint.light``, ...) so apps that support dual-theme rendering
    can reference both palettes in one file.

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
            # Active-theme aliases so templates keep using .flint.resolved
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
