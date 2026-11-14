#!/usr/bin/env python3
"""Regression suite: math spans must survive prettier-math byte for byte.

The suite has two layers:

* unit checks on the masker itself: fences, inline code, token widths, and a
  full mask/unmask round trip;
* end-to-end formatting of every file in ``corpus/``, checking math spans,
  dollar counts, token leaks, table alignment, and idempotency.

Run after changing the wrapper, the config, or the pinned Prettier version:

    python3 tests/prettier-math/run.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WRAPPER = Path.home() / ".local/bin/prettier-math"
CONFIG = Path.home() / ".config/prettier/config.json"

MATH = re.compile(
    r"(?<!\\)\$\$(?:(?!\$\$).)*?(?<!\\)\$\$"
    r"|(?<!\\)\\\[(?:(?!\\\]).)*?(?<!\\)\\\]"
    r"|(?<!\\)\\\((?:(?!\\\)).)*?(?<!\\)\\\)"
    r"|(?<!\\)\$(?!\$)(?:\\.|[^$\n\\])+?(?<!\\)\$",
    re.DOTALL,
)

# These files intentionally contain no closed math span.
ZERO_SPAN_CASES = {
    "29-escaped-dollar.md",
    "33-unclosed.md",
    "43-display-unclosed.md",
}

TOKEN_MARKERS = ("\ue000", "\ue001", "PRETTIERMATH")


def spans(text: str) -> list[str]:
    return [match.group(0) for match in MATH.finditer(text)]


def load_wrapper():
    loader = SourceFileLoader("prettier_math", str(WRAPPER))
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


def split_row(line: str) -> list[str]:
    text = line.strip().removeprefix("|").removesuffix("|")
    cells: list[str] = []
    buffer: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            buffer.append("\\")
            buffer.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(char)
    cells.append("".join(buffer).strip())
    return cells


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def table_problems(text: str) -> list[str]:
    problems: list[str] = []
    lines = text.splitlines()
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|") or not is_separator(
            lines[index + 1]
        ):
            index += 1
            continue

        block: list[str] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            block.append(lines[index])
            index += 1

        rows = [split_row(line) for line in block]
        separator = rows[1]
        for column, cell in enumerate(separator):
            widths = [
                len(row[column])
                for number, row in enumerate(rows)
                if number != 1 and column < len(row)
            ]
            widest = max(widths, default=0)
            if widest and len(cell.strip().strip(":")) > widest + 2:
                problems.append(
                    f"table column {column + 1} separator is "
                    f"{len(cell.strip().strip(':'))} wide for {widest} of content"
                )
    return problems


def unit_checks(module) -> list[str]:
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    fences = module.split_fences("```text\n$x^*$\n```\n\n$y^*$\n")
    check("backtick fence split", [fenced for fenced, _ in fences] == [True, False])

    fences = module.split_fences("~~~\n$x^*$\n~~~\n")
    check("tilde fence split", [fenced for fenced, _ in fences] == [True])

    check("inline code is not math", module.has_math("`$x^*$`") is False)
    check("fenced code is not math", module.has_math("```\n$x^*$\n```") is False)
    check("prose math is math", module.has_math("$x^*$") is True)

    fixture = (
        "# Fixture\n\n"
        "$a^*$ and $$b^*$$ and \\(c^*\\) and \\[d^*\\] and \\$e^*\\$.\n\n"
        "```text\n$f^*$\n```\n"
    )
    masked, store = module.mask(fixture, "TEST")
    check("mask round trip", module.unmask(masked, store) == fixture)
    check("mask produces tokens", bool(store))
    check(
        "tokens keep source width",
        all(len(token) == len(original) for token, original in store.items()),
    )
    check(
        "fenced code is untouched",
        "```text\n$f^*$\n```" in masked,
    )

    adjacent = "$x^*$$y^*$ and \\$z^*\\$"
    _, adjacent_store = module.mask(adjacent, "TEST")
    check("adjacent and escaped spans masked", len(adjacent_store) == 3)

    code_masked, code_store = module.mask("`$x^*$` and $y^*$", "TEST")
    check("inline code is masked as code", "`$x^*$`" in code_store.values())
    check("inline code leaves no raw span", "`$x^*$`" not in code_masked)

    display_masked, display_store = module.mask("Before $$x^*$$ after.", "TEST")
    check("display span tokenised", "$$x^*$$" in display_store.values())
    check("display leaves no dollar signs", "$" not in display_masked)

    return failures


def format_copy(wrapper: Path, destination: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(wrapper), "--write", "--config", str(CONFIG), str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    if not WRAPPER.is_file():
        print(f"prettier-math not found at {WRAPPER}", file=sys.stderr)
        return 1
    if not CONFIG.is_file():
        print(f"config not found at {CONFIG}", file=sys.stderr)
        return 1

    module = load_wrapper()
    failures = unit_checks(module)
    cases = sorted((ROOT / "corpus" / "baseline").glob("*.md"))
    cases += sorted((ROOT / "corpus" / "edge").glob("*.md"))

    for source in cases:
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / source.name
            shutil.copyfile(source, copy)
            result = format_copy(WRAPPER, copy)
            if result.returncode != 0:
                failures.append(f"{source.name}: wrapper failed")
                continue

            before = source.read_text(encoding="utf-8")
            after = copy.read_text(encoding="utf-8")
            if spans(after) != spans(before):
                failures.append(f"{source.name}: math changed")
            if after.count("$") != before.count("$"):
                failures.append(f"{source.name}: dollar count changed")
            if any(marker in after for marker in TOKEN_MARKERS):
                failures.append(f"{source.name}: token leaked")
            if not spans(before) and source.name not in ZERO_SPAN_CASES:
                failures.append(f"{source.name}: no math span to test")
            for problem in table_problems(after):
                failures.append(f"{source.name}: {problem}")

            again = Path(temporary) / "again.md"
            again.write_text(after, encoding="utf-8")
            if format_copy(WRAPPER, again).returncode != 0:
                failures.append(f"{source.name}: second pass failed")
            elif again.read_text(encoding="utf-8") != after:
                failures.append(f"{source.name}: not idempotent")

    print(f"{len(cases)} cases, {len(failures)} failure(s)")
    for failure in failures:
        print(f"  {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
