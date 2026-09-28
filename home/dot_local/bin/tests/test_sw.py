#!/usr/bin/env python3
"""Unit tests for the sw wallpaper utility.

Covers pure logic only (no lutgen/awww/feh subprocesses): output naming,
queue/history helpers, palette resolution, animation passthrough,
transition selection, wallpaper backend selection, and argument
parsing.

Run from the repository root::

    python3 home/dot_local/bin/tests/test_sw.py

Or via::

    make check-sw
"""

import importlib.machinery
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SW = _HERE.parent / "executable_sw"


def _load():
    # executable_sw has no .py suffix, so the loader must be explicit.
    loader = importlib.machinery.SourceFileLoader("sw", str(_SW))
    spec = importlib.util.spec_from_file_location("sw", str(_SW), loader=loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sw"] = module
    spec.loader.exec_module(module)
    return module


sw = _load()
_failures = 0


def check(name, cond, extra=""):
    global _failures
    if cond:
        print(f"[PASS] {name}")
    else:
        _failures += 1
        print(f"[FAIL] {name} {extra}")


def test_output_path(tmpdir):
    img = Path(tmpdir) / "river.jpg"
    img.write_bytes(b"\xff\xd8fake")
    out = sw.build_output_path(Path(tmpdir), "renderhash1234", img)
    check("output stem", out.stem.startswith("river."))
    check("output suffix", out.suffix == ".jpg")
    check("output has render hash", "renderhash1234" in out.stem)
    again = sw.build_output_path(Path(tmpdir), "renderhash1234", img)
    check("output deterministic", out == again)


def test_lines(tmpdir):
    path = Path(tmpdir) / "queue"
    sw.write_lines_atomic(path, ["b", "a", ""])
    check("write skips blank", sw.read_lines(path) == ["b", "a"])
    sw.write_lines_atomic(path, [])
    check("write empty", path.read_text() == "" and sw.read_lines(path) == [])
    check("read missing", sw.read_lines(Path(tmpdir) / "nope") == [])


def test_pop_next(tmpdir):
    present = Path(tmpdir) / "a.png"
    present.write_bytes(b"x")
    missing = str(Path(tmpdir) / "gone.png")
    chosen, rest = sw.pop_next([missing, str(present), str(present)])
    check("pop skips unreadable", chosen == str(present))
    check("pop keeps rest", rest == [str(present)])
    chosen, rest = sw.pop_next([missing])
    check("pop empty", chosen is None and rest == [])


def test_history(tmpdir):
    env = dict(os.environ, XDG_CACHE_HOME=tmpdir, XDG_RUNTIME_DIR=tmpdir)
    sw.push_history("a", env)
    sw.push_history("a", env)
    check("history dedupes consecutive", sw.read_lines(sw.history_file(env)) == ["a"])
    sw.push_history("b", env)
    check("history appends", sw.read_lines(sw.history_file(env)) == ["a", "b"])
    check("current empty", sw.current_wallpaper(env) is None)
    sw.record_last_wallpaper("b", env)
    check("current recorded", sw.current_wallpaper(env) == "b")


def test_pool_scan(tmpdir):
    pool = Path(tmpdir) / "pool"
    pool.mkdir()
    (pool / "b.png").write_bytes(b"x")
    (pool / "a.jpg").write_bytes(b"x")
    (pool / "note.txt").write_bytes(b"x")
    (pool / "anim.webp").write_bytes(b"x")
    (pool / "c.gif").write_bytes(b"x")
    got = sw.get_wallpapers(pool)
    check(
        "pool sorted image-only",
        [Path(p).name for p in got] == ["a.jpg", "anim.webp", "b.png", "c.gif"],
    )
    check("pool missing", sw.get_wallpapers(Path(tmpdir) / "nope") == [])


def test_mode(tmpdir):
    env = {"HOME": str(tmpdir)}
    state = Path(tmpdir) / ".local" / "state"
    state.mkdir(parents=True)

    check("mode missing file", sw.palette_mode(env) == "dark")
    (state / "palette-mode").write_text("light\n")
    check("mode from state file", sw.palette_mode(env) == "light")
    check(
        "pool follows mode",
        sw.pool_dir_for_mode(sw.palette_mode(env))
        == Path.home() / "Pictures" / "Wallpapers" / "pool_light",
    )
    check(
        "palette follows mode",
        sw.palette_for_mode("light") == "neutral-light"
        and sw.palette_for_mode("dark") == "neutral",
    )
    env["SW_MODE"] = "dark"
    check("SW_MODE override", sw.palette_mode(env) == "dark")
    queue_dark = sw.queue_file(env)
    last_dark = sw.last_file(env)
    env["SW_MODE"] = "light"
    queue_light = sw.queue_file(env)
    last_light = sw.last_file(env)
    check(
        "queue file mode-scoped",
        queue_dark.name == "queue-dark"
        and queue_light.name == "queue-light"
        and queue_dark != queue_light,
    )
    check(
        "last file mode-scoped",
        last_dark.name == "last-dark"
        and last_light.name == "last-light"
        and last_dark != last_light,
    )
    (state / "palette-mode").write_text("bogus\n")
    env.pop("SW_MODE")
    check("mode garbage falls back dark", sw.palette_mode(env) == "dark")


def test_restore_target(tmpdir):
    env = {"HOME": str(tmpdir)}
    state = Path(tmpdir) / ".local" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "palette-mode").write_text("dark\n")

    recorded = Path(tmpdir) / "recorded.jpg"
    recorded.write_bytes(b"x")
    check(
        "restore uses the readable record",
        sw.restore_target(env, str(recorded)) == str(recorded),
    )


def test_palette(tmpdir):
    lutgen_dir = Path(tmpdir) / "lutgen"
    lutgen_dir.mkdir()
    pal = lutgen_dir / "neutral"
    pal.write_text("101010\n")
    src = sw.resolve_palette_source(lutgen_dir, "neutral")
    check("palette file argument", src.argument == "neutral")
    check("palette identity", src.identity == str(pal.resolve()))
    src = sw.resolve_palette_source(lutgen_dir, "builtin-name")
    check(
        "palette builtin passthrough",
        src.argument == "builtin-name" and src.content_hash == "builtin",
    )
    explicit = Path(tmpdir) / "custom.txt"
    explicit.write_text("FFFFFF\n")
    src = sw.resolve_palette_source(lutgen_dir, str(explicit))
    check("palette explicit path", src.argument == str(explicit))
    try:
        sw.resolve_palette_source(lutgen_dir, str(Path(tmpdir) / "missing.txt"))
        check("palette missing dies", False)
    except SystemExit:
        check("palette missing dies", True)


def test_animation(tmpdir):
    gif = Path(tmpdir) / "orbit.gif"
    gif.write_bytes(b"GIF89afake")
    check("gif is animation", sw.is_animation(gif))
    check("upper gif is animation", sw.is_animation(Path("X.GIF")))
    check("jpg is not animation", not sw.is_animation(Path("a.jpg")))
    check("gif cuts transition", sw.transition_for(gif) == ("0", "none"))
    check(
        "still keeps transition",
        sw.transition_for(Path("a.jpg")) == ("0.6", "random"),
    )
    outdir = Path(tmpdir) / "cached"
    outdir.mkdir()
    first = sw.passthrough_animation(outdir, gif)
    check("passthrough caches", first is not None and first.is_file())
    check("passthrough keeps suffix", first is not None and first.suffix == ".gif")
    check(
        "passthrough content identical",
        first is not None and first.read_bytes() == gif.read_bytes(),
    )
    second = sw.passthrough_animation(outdir, gif)
    check("passthrough stable name", second == first)
    missing = sw.passthrough_animation(outdir, Path(tmpdir) / "gone.gif")
    check("passthrough missing dies softly", missing is None)


def test_args():
    args = sw.parse_args(["--next"])
    check("parse next", args.next and not args.prev and args.images == [])
    args = sw.parse_args(["--prev"])
    check("parse prev", args.prev and not args.next)
    args = sw.parse_args(["--restore"])
    check("parse restore", args.restore and not args.next and not args.prev)
    args = sw.parse_args(["a.jpg", "--set"])
    check(
        "parse images+set", list(args.images) == [Path("a.jpg")] and args.set_wallpaper
    )
    check("rbf default", args.rbf is True)
    args = sw.parse_args(["--blur", "a.jpg"])
    check("blur flips rbf", args.rbf is False)
    try:
        sw.parse_args(["--next", "--prev"])
        check("next/prev exclusive", False)
    except SystemExit:
        check("next/prev exclusive", True)
    try:
        sw.parse_args(["--restore", "--next"])
        check("restore exclusive", False)
    except SystemExit:
        check("restore exclusive", True)


def test_numbers():
    check("normalize", sw.normalize_number("lum", "1.05") == "1.05")
    try:
        sw.normalize_number("lum", "nope")
        check("normalize dies", False)
    except SystemExit:
        check("normalize dies", True)


def test_backend():
    def which_awww(name):
        return "/usr/bin/awww" if name == "awww" else None

    def which_feh(name):
        return "/usr/sbin/feh" if name == "feh" else None

    def which_both(name):
        return f"/usr/bin/{name}"

    def which_none(name):
        return None

    check(
        "backend prefers awww",
        sw.wallpaper_backend(which_awww) == ("awww", "/usr/bin/awww"),
    )
    check(
        "backend falls back to feh",
        sw.wallpaper_backend(which_feh) == ("feh", "/usr/sbin/feh"),
    )
    check(
        "backend awww wins when both exist",
        sw.wallpaper_backend(which_both) == ("awww", "/usr/bin/awww"),
    )
    check("backend missing", sw.wallpaper_backend(which_none) is None)


def test_fehbg():
    home = "/home/tester"
    out = sw.fehbg_content(Path("/home/tester/.cache/sw/wallpapers/x.png"), home)
    check("fehbg home-relative", '"$HOME/.cache/sw/wallpapers/x.png"' in out)
    check(
        "fehbg script form",
        out.startswith("#!/bin/sh\n")
        and "--no-fehbg" in out
        and "feh --no-fehbg --bg-fill" in out,
    )
    out = sw.fehbg_content(Path("/elsewhere/x.png"), home)
    check("fehbg absolute passthrough", '"/elsewhere/x.png"' in out)


def main():
    with tempfile.TemporaryDirectory(prefix="sw_test_") as tmpdir:
        test_output_path(tmpdir)
        test_lines(tmpdir)
        test_pop_next(tmpdir)
        test_history(tmpdir)
        test_pool_scan(tmpdir)
        test_animation(tmpdir)
        test_mode(tmpdir)
        test_restore_target(tmpdir)
        test_palette(tmpdir)
    test_args()
    test_numbers()
    test_backend()
    test_fehbg()
    print("ALL PASS" if _failures == 0 else "SOME FAILED")
    sys.exit(0 if _failures == 0 else 1)


if __name__ == "__main__":
    main()
