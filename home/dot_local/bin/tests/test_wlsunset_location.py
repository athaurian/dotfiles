#!/usr/bin/env python3

import importlib.machinery
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "executable_wlsunset-location"
_REPO = _HERE.parents[3]


def _load():
    name = "wlsunset_location"
    loader = importlib.machinery.SourceFileLoader(name, str(_SCRIPT))
    spec = importlib.util.spec_from_file_location(name, str(_SCRIPT), loader=loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mod = _load()
_ORIGINAL_FETCH = mod.fetch
_ORIGINAL_GEOCLUE = mod.source_geoclue
_ORIGINAL_RESTART = mod.restart_service
_failures = 0


def check(name, cond, extra=""):
    global _failures
    if cond:
        print(f"[PASS] {name}")
    else:
        _failures += 1
        print(f"[FAIL] {name} {extra}")


def exit_code(fn):
    try:
        fn()
    except SystemExit as exc:
        return exc.code
    return 0


def test_coordinates():
    check("valid pair", mod.valid_coord_pair("13.75", "100.5"))
    check("valid boundaries", mod.valid_coord_pair("-90", "180"))
    check("lat out of range", not mod.valid_coord_pair("90.01", "0"))
    check("lon out of range", not mod.valid_coord_pair("0", "-180.01"))
    check("scientific notation rejected", not mod.valid_coord_pair("1e2", "0"))
    check("non-numeric rejected", not mod.valid_coord_pair("north", "east"))
    check("empty rejected", not mod.valid_coord_pair("", ""))

    check("round two", mod.round_coord("13.756", 2) == "13.76")
    check("round zero pads", mod.round_coord("100.5", 2) == "100.50")
    check("round zero digits", mod.round_coord("13.6", 0) == "14")


def test_provider_payloads():
    loc = mod.provider_coordinates('{"loc": "13.75,100.5"}', "loc")
    check("loc style", loc == ("13.75", "100.5"), loc)

    loc = mod.provider_coordinates('{"loc": "13.75, 100.5"}', "loc")
    check("loc style trims", loc == ("13.75", "100.5"), loc)

    check(
        "loc without comma",
        mod.provider_coordinates('{"loc": "13.75"}', "loc") is None,
    )
    check(
        "loc non-string",
        mod.provider_coordinates('{"loc": [13.75, 100.5]}', "loc") is None,
    )
    check(
        "loc out of range",
        mod.provider_coordinates('{"loc": "95,100.5"}', "loc") is None,
    )
    check("malformed json", mod.provider_coordinates("{", "kv") is None)
    check("json array", mod.provider_coordinates("[]", "kv") is None)

    kv = mod.provider_coordinates('{"latitude": 13.75, "longitude": 100.5}', "kv")
    check("kv style", kv == ("13.75", "100.5"), kv)
    check(
        "kv null latitude",
        mod.provider_coordinates('{"latitude": null, "longitude": 100.5}', "kv")
        is None,
    )
    check(
        "kv missing longitude",
        mod.provider_coordinates('{"latitude": 13.75}', "kv") is None,
    )
    check(
        "kv non-numeric",
        mod.provider_coordinates('{"latitude": "north", "longitude": 100.5}', "kv")
        is None,
    )


def test_geoclue_parse():
    text = "Location:\n  Latitude: 13.7563\n  Longitude: -100.5018\n"
    check("geoclue latitude", mod._coordinate_from_text(text, "atitude") == "13.7563")
    check(
        "geoclue longitude",
        mod._coordinate_from_text(text, "ongitude") == "-100.5018",
    )
    check("geoclue missing", mod._coordinate_from_text("nothing", "atitude") == "")


def test_guard():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        target = root / "nested" / "wlsunset.env"
        code = exit_code(lambda: mod.guard_target(str(target), False))
        check("guard refuses source tree", code == 3, code)
        check(
            "guard force overrides",
            exit_code(lambda: mod.guard_target(str(target), True)) == 0,
        )

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "wlsunset.env"
        check(
            "guard allows plain dir",
            exit_code(lambda: mod.guard_target(str(target), False)) == 0,
        )


def test_write_env():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "state" / "wlsunset.env"
        mod.write_env(str(target), "13.76", "100.50", "manual")
        text = target.read_text()
        mode = stat.S_IMODE(target.stat().st_mode)
        check("write creates file", target.is_file())
        check("write mode 0600", mode == 0o600, oct(mode))
        check("write header source", "(manual source)" in text)
        check("write latitude", 'WLSUNSET_LATITUDE="13.76"' in text)
        check("write longitude", 'WLSUNSET_LONGITUDE="100.50"' in text)


def test_manual_main():
    calls = []
    mod.restart_service = lambda: calls.append("restart")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "wlsunset.env"
        code = exit_code(
            lambda: mod.main(
                ["--lat", "13.756", "--lon", "100.504", "-p", "2", "-o", str(target)]
            )
        )
        text = target.read_text() if target.exists() else ""
        check("manual exit 0", code == 0, code)
        check("manual source", "(manual source)" in text)
        check("manual rounds latitude", 'WLSUNSET_LATITUDE="13.76"' in text)
        check("manual rounds longitude", 'WLSUNSET_LONGITUDE="100.50"' in text)
        check("manual restarts service", calls == ["restart"], calls)


def test_provider_fallback():
    calls = []

    def fake_fetch(url, timeout):
        calls.append(url)
        if "ipinfo" in url:
            return '{"loc": "not a pair"}'
        if "geojs" in url:
            return json.dumps({"latitude": 13.75, "longitude": 100.5})
        return None

    mod.fetch = fake_fetch
    mod.source_geoclue = lambda timeout: None
    mod.restart_service = lambda: None
    old = os.environ.get("WLSUNSET_GEO_PROVIDERS")
    os.environ["WLSUNSET_GEO_PROVIDERS"] = "ipinfo geojs ipapi"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "wlsunset.env"
            code = exit_code(lambda: mod.main(["-o", str(target)]))
            text = target.read_text() if target.exists() else ""
            check("fallback exit 0", code == 0, code)
            check("fallback used geojs", "(geojs source)" in text)
            check("fallback skipped ipapi", not any("ipapi" in url for url in calls))
            check("fallback order", len(calls) == 2 and "ipinfo" in calls[0], calls)
    finally:
        if old is None:
            os.environ.pop("WLSUNSET_GEO_PROVIDERS", None)
        else:
            os.environ["WLSUNSET_GEO_PROVIDERS"] = old
        mod.fetch = _ORIGINAL_FETCH
        mod.source_geoclue = _ORIGINAL_GEOCLUE


def test_restart_service():
    calls = []
    holder = {"state": "inactive"}

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[2] == "show":
            return SimpleNamespace(returncode=0, stdout=holder["state"] + "\n")
        return SimpleNamespace(returncode=0, stdout="")

    original_subprocess = mod.subprocess
    original_shutil = mod.shutil
    mod.subprocess = SimpleNamespace(run=fake_run)
    mod.shutil = SimpleNamespace(which=lambda name: "/usr/bin/systemctl")
    try:
        for state in ("inactive", "activating"):
            calls.clear()
            holder["state"] = state
            _ORIGINAL_RESTART()
            restarts = [cmd for cmd in calls if cmd[2] == "restart"]
            check(f"restart skipped when {state}", restarts == [], calls)

        calls.clear()
        holder["state"] = "active"
        _ORIGINAL_RESTART()
        restarts = [cmd for cmd in calls if cmd[2] == "restart"]
        check("restart runs when active", len(restarts) == 1, calls)
        check("restart does not block", "--no-block" in restarts[0], restarts)
    finally:
        mod.subprocess = original_subprocess
        mod.shutil = original_shutil


def test_no_source_keeps_file():
    mod.fetch = lambda url, timeout: None
    mod.source_geoclue = lambda timeout: None
    mod.restart_service = lambda: None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "wlsunset.env"
            target.write_text("sentinel\n")
            code = exit_code(lambda: mod.main(["-o", str(target)]))
            check("no source exit 2", code == 2, code)
            check("no source keeps file", target.read_text() == "sentinel\n")
    finally:
        mod.fetch = _ORIGINAL_FETCH
        mod.source_geoclue = _ORIGINAL_GEOCLUE


def test_cli():
    def run(args):
        return subprocess.run(
            [sys.executable, str(_SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    help_proc = run(["--help"])
    check("cli help exit 0", help_proc.returncode == 0)
    check("cli help documents exit codes", "Exit codes:" in help_proc.stdout)

    with tempfile.TemporaryDirectory() as tmp:
        never = str(Path(tmp) / "never.env")
        precision = run(["-p", "9", "-o", never])
        check("cli precision exit 1", precision.returncode == 1, precision.returncode)
        check(
            "cli precision message",
            "precision must be between 0 and 6" in precision.stderr,
        )

        pair = run(["--lat", "13.75", "-o", never])
        check("cli pair exit 1", pair.returncode == 1, pair.returncode)
        check(
            "cli pair message",
            "--lat and --lon must be given together" in pair.stderr,
        )

    guard_target = _REPO / f".wlsunset-test-{os.getpid()}.env"
    guard_target.unlink(missing_ok=True)
    try:
        guard = run(["--lat", "13.75", "--lon", "100.5", "-o", str(guard_target)])
        check("cli guard exit 3", guard.returncode == 3, guard.returncode)
        check("cli guard wrote nothing", not guard_target.exists())
    finally:
        guard_target.unlink(missing_ok=True)


def main():
    test_coordinates()
    test_provider_payloads()
    test_geoclue_parse()
    test_guard()
    test_write_env()
    test_manual_main()
    test_restart_service()
    test_provider_fallback()
    test_no_source_keeps_file()
    test_cli()
    ok = _failures == 0
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
