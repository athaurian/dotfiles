#!/usr/bin/env python3
"""Regression suite: math spans must survive prettier-math byte for byte.

Run after changing the wrapper, the config, or the pinned Prettier version:

    python3 tests/prettier-math/run.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WRAPPER = Path.home() / ".local/bin/prettier-math"
CONFIG = Path.home() / ".config/prettier/config.json"

MATH = re.compile(
    r"(?<!\\)\$\$(?:(?!\$\$).)*?(?<!\\)\$\$"
    r"|(?<!\\)\\\[(?:(?!\\\]).)*?(?<!\\)\\\]"
    r"|(?<!\\)\\\((?:(?!\\\)).)*?(?<!\\)\\\)"
    r"|(?<![\\$])\$(?!\$)(?:\\.|[^$\n\\])+?(?<!\\)\$",
    re.DOTALL,
)


def spans(text: str) -> list[str]:
    return [match.group(0) for match in MATH.finditer(text)]


def main() -> int:
    if not WRAPPER.is_file():
        print(f"prettier-math not found at {WRAPPER}", file=sys.stderr)
        return 1
    if not CONFIG.is_file():
        print(f"config not found at {CONFIG}", file=sys.stderr)
        return 1

    cases = sorted((ROOT / "corpus" / "baseline").glob("*.md"))
    cases += sorted((ROOT / "corpus" / "edge").glob("*.md"))
    failures: list[str] = []

    for source in cases:
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / source.name
            shutil.copyfile(source, copy)
            result = subprocess.run(
                [str(WRAPPER), "--write", "--config", str(CONFIG), str(copy)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failures.append(f"{source.name}: wrapper failed")
                continue
            if spans(copy.read_text(encoding="utf-8")) != spans(
                source.read_text(encoding="utf-8")
            ):
                failures.append(f"{source.name}: math changed")

    print(f"{len(cases)} cases, {len(failures)} failure(s)")
    for failure in failures:
        print(f"  {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
