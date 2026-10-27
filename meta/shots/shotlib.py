"""Shared helpers for the screenshot capture scripts."""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parent.parent.parent
CAPTURES = ROOT / "meta" / "captures"
DOC_IMAGES = ROOT / "docs" / "images"
HL_TEST = ROOT / "assets" / "hl_test.py"
SHOT_TMP = Path("/tmp/chezmoi-shots")
HERO_SOCKET = SHOT_TMP / "nvim-hero.sock"
EDITOR_SOCKET = SHOT_TMP / "editor.sock"
CLIP_DIR = SHOT_TMP / "cliphist-demo"
CLIP_DB = CLIP_DIR / "db"
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

SHOT_TMP.mkdir(parents=True, exist_ok=True)
CAPTURES.mkdir(parents=True, exist_ok=True)


def error(message: str) -> NoReturn:
    raise SystemExit(f"shots: {message}")


def run(
    argv: list[str],
    *,
    check: bool = True,
    input: bytes | None = None,
    capture: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        check=check,
        input=input,
        stdout=subprocess.PIPE if capture else None,
        cwd=cwd,
    )


def run_pillow(script: str, *args: str) -> None:
    run(
        [
            "uv",
            "run",
            "--with",
            "pillow",
            "python3",
            str(ROOT / "meta" / script),
            *args,
        ],
        cwd=ROOT,
    )


def sway(*args: str) -> None:
    subprocess.run(
        ["swaymsg", *args],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def sway_exec(argv: list[str]) -> None:
    sway("exec", shlex.join(argv))


def sway_tree() -> dict[str, Any]:
    result = subprocess.run(
        ["swaymsg", "-t", "get_tree"],
        check=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def walk(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield node
    for key in ("nodes", "floating_nodes"):
        for child in node.get(key, ()):
            yield from walk(child)


def find_window(
    *, app_id: str | None = None, title: str | None = None
) -> dict[str, Any] | None:
    for node in walk(sway_tree()):
        if app_id is not None and node.get("app_id") == app_id:
            return node
        if title is not None and node.get("name") == title:
            return node
    return None


def wait_window(
    *,
    app_id: str | None = None,
    title: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        node = find_window(app_id=app_id, title=title)
        if node is not None:
            return node
        if time.monotonic() >= deadline:
            error(f"window {app_id or title!r} did not appear")
        time.sleep(0.1)


def wait_socket(path: Path, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.is_socket():
        if time.monotonic() >= deadline:
            error(f"socket did not appear: {path}")
        time.sleep(0.1)


def nvim_remote_expr(socket: Path, expression: str) -> str:
    result = run(
        ["timeout", "5", "nvim", "--server", str(socket), "--remote-expr", expression],
        capture=True,
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


def nvim_remote_send(socket: Path, keys: str) -> None:
    run(["timeout", "5", "nvim", "--server", str(socket), "--remote-send", keys])


def nvim_cursor(socket: Path) -> tuple[int, int]:
    line = nvim_remote_expr(socket, "line('.')")
    column = nvim_remote_expr(socket, "col('.')")
    try:
        return int(line), int(column)
    except ValueError:
        error(f"could not read cursor position: {line}:{column}")


def verify_editor(socket: Path, *, path: Path, minimum_lines: int = 100) -> None:
    buffer = nvim_remote_expr(socket, 'expand("%:p")')
    try:
        lines = int(nvim_remote_expr(socket, 'line("$")'))
    except ValueError:
        error("could not read the editor line count")
    if buffer != str(path) or lines < minimum_lines:
        error(
            f"editor is {buffer} with {lines} lines, expected {path} with {minimum_lines} or more"
        )


def prime_editor(
    socket: Path,
    *,
    line: int = 330,
    column: int = 12,
    settle: float = 0.3,
) -> None:
    nvim_remote_expr(
        socket,
        'execute("wincmd l") + execute("normal! ggzt") + execute("redraw!")',
    )
    time.sleep(settle)
    nvim_remote_expr(
        socket,
        f'execute("call cursor({line}, {column})") '
        f'+ execute("normal! zz") '
        f'+ execute("redraw!")',
    )
    time.sleep(settle)
    actual_line, actual_column = nvim_cursor(socket)
    if actual_line != line or actual_column != column:
        error(
            f"editor cursor is {actual_line}:{actual_column}, expected {line}:{column}"
        )


def close_notifications() -> None:
    subprocess.run(
        ["dunstctl", "close-all"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["dunstctl", "count", "displayed"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stdout.strip() == "0":
            time.sleep(0.2)
            return
        time.sleep(0.05)


def palette_mode(mode: str) -> None:
    state = Path.home() / ".local/state/palette-mode"
    try:
        current = state.read_text(encoding="utf-8").strip()
    except OSError:
        current = ""
    if current != mode:
        run([str(Path.home() / ".local/bin/palette-mode"), mode])
        time.sleep(0.6)
    close_notifications()


def grim(path: Path, *options: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    run(["grim", *options, str(path)])


def magick(*args: str) -> None:
    run(["magick", *args])


def mode_suffix(mode: str) -> str:
    return "-light" if mode == "light" else ""


def mode_background(mode: str) -> str:
    return "f3efec" if mode == "light" else "050505"


def mode_edge(mode: str) -> str:
    return "999999" if mode == "light" else "5a5a5a"


def kill_pid(pid: int | None) -> None:
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def kill_window(*, app_id: str | None = None, title: str | None = None) -> None:
    node = find_window(app_id=app_id, title=title)
    if node is not None:
        kill_pid(node.get("pid"))


def focused_kitty_geom() -> str:
    for node in walk(sway_tree()):
        if node.get("focused") and node.get("app_id") == "kitty":
            rect = node["rect"]
            return f"{rect['width']}x{rect['height']}+{rect['x']}+{rect['y']}"
    error("no focused kitty window")


def window_geom_by_title(title: str) -> str:
    node = find_window(title=title)
    if node is None:
        error(f"window {title!r} not found")
    rect = node["rect"]
    return f"{rect['width']}x{rect['height']}@{rect['x']},{rect['y']}"


def write_geom(path: Path, value: str) -> None:
    path.write_text(value + "\n", encoding="utf-8")


def crop_round(
    source: Path,
    output: Path,
    *,
    crop: str,
    radius: float,
    edge: str,
    background: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_pillow(
        "round-corners.py",
        str(source),
        str(output),
        "--crop",
        crop,
        "--radius",
        str(radius),
        "--edge",
        edge,
        "--background",
        background,
    )


def run_main(main: Callable[[], None]) -> None:
    try:
        main()
    except subprocess.CalledProcessError as exc:
        cmd = exc.cmd if isinstance(exc.cmd, list) else [str(exc.cmd)]
        print(
            f"shots: command failed ({exc.returncode}): "
            f"{shlex.join([str(part) for part in cmd])}",
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode) from None
    except FileNotFoundError as exc:
        print(f"shots: missing {exc.filename}", file=sys.stderr)
        raise SystemExit(1) from None
