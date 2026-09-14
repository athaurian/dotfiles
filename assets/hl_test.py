#!/usr/bin/env python3
"""Highlight test: one of everything, for eyeballing a colorscheme."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, ClassVar, Final, ParamSpec, TypeVar

# TODO: retire the legacy code path below
# NOTE: remember to update the docs afterwards
# FIXME: this regex rejects valid input -- see issue #42

CONSTANT: Final[int] = 0xDEAD_BEEF
PI_APPROX = 3.14159
NOTHING: None = None
FLAG = True

T = TypeVar("T")
P = ParamSpec("P")


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


@dataclass
class Palette:
    """A small palette with defaults and slots."""

    name: str
    colors: list[str] = field(default_factory=list)
    count: ClassVar[int] = 0

    def __post_init__(self) -> None:
        self.count = len(self.colors)

    @property
    def primary(self) -> str | None:
        return self.colors[0] if self.colors else None

    @classmethod
    def empty(cls, name: str = "blank") -> Palette:
        return cls(name=name)

    @staticmethod
    def describe() -> str:
        return "a palette of colors"


def deprecated(reason: str):  # decorator with arguments
    def deco(fn):
        @wraps(fn)
        def inner(*args: P.args, **kwargs: P.kwargs):
            print(f"deprecated: {reason}", file=sys.stderr)
            return fn(*args, **kwargs)

        return inner

    return deco


@lru_cache(maxsize=128)
def shade(hex_color: str, factor: float = 0.5) -> tuple[int, int, int]:
    """Mix a #rrggbb color toward black."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (int(r * factor), int(g * factor), int(b * factor))


@deprecated("use shade() instead")
def old_shade(hex_color):
    return hex_color


async def fetch_all(paths: list[Path]) -> dict[str, bytes]:
    results: dict[str, bytes] = {}
    async with asyncio.TaskGroup() as tg:
        tasks = {tg.create_task(_read(p)): p for p in paths}
    for task, path in tasks.items():
        results[str(path)] = task.result()
    return results


async def _read(path: Path) -> bytes:
    return await asyncio.to_thread(path.read_bytes)


def classify(value: Any) -> str:
    match value:
        case None:
            return "none"
        case True | False:
            return "bool"
        case int() | float() if value < 0:
            return "negative number"
        case {"key": str(k), **rest}:
            return f"dict with {k} and {len(rest)} more"
        case [first, *tail]:
            return f"list starting with {first!r} ({len(tail)} rest)"
        case str() as text if text.startswith("http"):
            return "url"
        case _:
            return "other"


def main(argv: list[str]) -> int:
    palette = Palette("demo", ["#E05561", "#8CC265", "#4AA5F0"])
    total = sum(range(1, 101))
    squares = [x * x for x in range(10) if x % 2 == 0]
    mapping = {c.name: c.value for c in Color}
    gen = (f"item-{i}" for i in range(3))
    text = f"name={palette.name!r} total={total:,}"
    raw = r"C:\no\escapes\here"
    blob = b"\x00\xff binary \n data"
    assert palette.primary is not None, "palette must not be empty"
    try:
        risky = 10 / 0
    except ZeroDivisionError as exc:
        print(f"caught: {exc!r}")
        raise SystemExit(1) from exc
    finally:
        print("done")
    print(text, raw, blob, squares, mapping, list(gen), risky)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
