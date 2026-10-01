#!/usr/bin/env python3

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "executable_mpris.py"
_FAKE_PLAYERCTL = (
    _HERE.parent.parent.parent / "waybar" / "scripts" / "tests" / "fake_playerctl.py"
)
_F = "\x1f"


def _line(player, status, pos, artist, title):
    return _F.join((player, status, pos, artist, title))


def _norm(line):
    paused = "%{T3}" in line
    text = re.sub(r"%\{[^}]*\}", "", line).strip()
    text = re.sub(r"^[󰐊󰏤]\s*", "", text)
    return text, paused


def _sc(events, delay=0.15):
    os_ev = [e if isinstance(e, dict) else {"line": e} for e in events]
    fw_ev = [e if isinstance(e, dict) else {"line": e, "delay": delay} for e in events]
    return {"oneshot": os_ev, "follow": fw_ev}


def _make_fakebin():
    tmpdir = Path(tempfile.mkdtemp(prefix="mpris_fake_"))
    fakebin = tmpdir / "bin"
    fakebin.mkdir()
    link = fakebin / "playerctl"
    shutil.copy(_FAKE_PLAYERCTL, link)
    link.chmod(0o755)
    return tmpdir, fakebin


SCENARIOS = {
    "track_change": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "2000000", "", ""),
                _line("chromium.i1", "Playing", "3000000", "Artist A", "Song Two"),
            ]
        ),
        "expected": [
            ("", False),
            ("Artist A - Song One", False),
            ("Artist A - Song Two", False),
        ],
    },
    "stale_status": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "5000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "5000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "5000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "6000000", "Artist A", "Song One"),
            ]
        ),
        "expected": [
            ("", False),
            ("Artist A - Song One", False),
            ("Artist A - Song One", True),
            ("Artist A - Song One", False),
        ],
    },
    "pause_blank": {
        "streams": _sc(
            [
                _line("chromium.i1", "Paused", "4000000", "Artist A", "Song One"),
                _line("chromium.i1", "Paused", "4000000", "", ""),
                _line("chromium.i1", "Paused", "4000000", "", ""),
                _line("chromium.i1", "Stopped", "", "", ""),
            ]
        ),
        "expected": [
            ("", False),
            ("Artist A - Song One", True),
            ("", False),
        ],
    },
    "player_gone": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "Song One"),
                {"exit": 1},
                _line("chromium.i2", "Playing", "2000000", "", ""),
            ]
        ),
        "expected": [
            ("", False),
            ("Artist A - Song One", False),
            ("", False),
        ],
    },
    "live_stream": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "0", "Radio", "Live Stream"),
                _line("chromium.i1", "Playing", "0", "Radio", "Live Stream"),
            ]
        ),
        "expected": [
            ("", False),
            ("Radio - Live Stream", False),
        ],
    },
    "transition_stop": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "Song One"),
                _line("chromium.i1", "Stopped", "", "", ""),
                _line("chromium.i1", "Playing", "3000000", "Artist A", "Song Two"),
            ]
        ),
        "expected": [
            ("", False),
            ("Artist A - Song One", False),
            ("Artist A - Song Two", False),
        ],
    },
    "follow_missed": {
        "streams": {
            "oneshot": [
                {
                    "line": _line(
                        "chromium.i1", "Playing", "1000000", "Artist A", "Song One"
                    )
                },
                {
                    "line": _line(
                        "chromium.i2", "Playing", "2000000", "Artist A", "Song Two"
                    )
                },
            ],
            "follow": [
                {
                    "line": _line(
                        "chromium.i1", "Playing", "1000000", "Artist A", "Song One"
                    ),
                    "delay": 0.15,
                },
            ],
        },
        "expected": [
            ("", False),
            ("Artist A - Song One", False),
            ("Artist A - Song Two", False),
        ],
    },
}


def _run_scenario(name, spec):
    tmpdir, fakebin = _make_fakebin()
    state_base = tmpdir
    streams = spec["streams"]

    for suffix in ("_os", "_fw"):
        (state_base / f"state_{name}{suffix}.json").unlink(missing_ok=True)

    scen = state_base / f"scen_{name}.json"
    with open(scen, "w") as fh:
        json.dump(streams, fh)

    env = dict(os.environ)
    env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
    env["MPRIS_POLL_INTERVAL"] = "0.15"
    env["MPRIS_STALL_MIN_TIME"] = "0.3"
    env["MPRIS_GRACE_SECONDS"] = "0.4"
    env["FAKE_SCENARIO"] = str(scen)
    env["FAKE_OS_STATE"] = str(state_base / f"state_{name}_os.json")
    env["FAKE_FW_STATE"] = str(state_base / f"state_{name}_fw.json")

    proc = subprocess.Popen(
        [sys.executable, str(_SCRIPT)],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    got = []
    deadline = time.time() + 10
    try:
        while time.time() < deadline:
            raw = proc.stdout.readline()
            if raw:
                got.append(_norm(raw))
                if len(got) >= len(spec["expected"]):
                    break
            elif proc.poll() is not None:
                break
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    shutil.rmtree(tmpdir, ignore_errors=True)

    exp = spec["expected"]
    ok = got == exp
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}")
    if not ok:
        print(f"  expected: {exp}")
        print(f"  got     : {got}")
    return ok


def main():
    ok = all(_run_scenario(name, spec) for name, spec in SCENARIOS.items())
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
