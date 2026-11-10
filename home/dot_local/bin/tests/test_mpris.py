#!/usr/bin/env python3

import html
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "executable_mpris"
_FAKE = _HERE / "fake_playerctl.py"
_F = "\x1f"

ICON_PLAYING = "󰐊"
ICON_PAUSED = "󰏤"
MODES = ("waybar", "polybar")


def _line(player, status, pos, artist, title):
    return _F.join((player, status, pos, artist, title))


def _norm_waybar(line):
    obj = json.loads(line)
    text = re.sub(r"<span>[^<]*</span>", "", obj["text"])
    italic = "<i>" in text
    text = re.sub(r"</?i>", "", text).strip()
    return html.unescape(text), italic, obj["class"]


def _norm_polybar(line):
    text = re.sub(r"%\{[^}]*\}", "", line).strip()
    paused = text.startswith(ICON_PAUSED)
    text = re.sub(r"^[󰐊󰏤]\s*", "", text)
    text = text.replace("%%", "%")
    if not text:
        status = "stopped"
    elif paused:
        status = "paused"
    else:
        status = "playing"
    return text, paused, status


_NORM = {"waybar": _norm_waybar, "polybar": _norm_polybar}


def _ev(player, status, pos, artist, title, delay=None):
    event = {"line": _line(player, status, pos, artist, title)}
    if delay is not None:
        event["delay"] = delay
    return event


def _sc(events, delay=0.15, poll=0.15):
    os_ev = [e if isinstance(e, dict) else {"line": e} for e in events]
    fw_ev = [e if isinstance(e, dict) else {"line": e, "delay": delay} for e in events]
    return {"oneshot": os_ev, "follow": fw_ev, "poll": poll}


def _readline(stream, deadline):
    remaining = deadline - time.time()
    if remaining <= 0:
        return ""
    ready, _, _ = select.select([stream], [], [], remaining)
    if not ready:
        return ""
    return stream.readline()


def _make_fakebin():
    tmpdir = Path(tempfile.mkdtemp(prefix="mpris_fake_"))
    fakebin = tmpdir / "bin"
    fakebin.mkdir()
    link = fakebin / "playerctl"
    shutil.copy(_FAKE, link)
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
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist A - Song Two", False, "playing"),
        ],
    },
    "missing_artist": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "2000000", "", "Video Title"),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Video Title", False, "playing"),
        ],
    },
    "missing_title": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "Song One"),
                _line("chromium.i1", "Playing", "2000000", "Artist B", ""),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist B", False, "playing"),
        ],
    },
    "stale_status": {
        "streams": {
            "oneshot": [
                _ev("chromium.i1", "Playing", "5000000", "Artist A", "Song One"),
                _ev("chromium.i1", "Playing", "5000000", "Artist A", "Song One"),
                _ev("chromium.i1", "Playing", "6000000", "Artist A", "Song One"),
            ],
            "follow": [
                _ev("chromium.i1", "Playing", "5000000", "Artist A", "Song One", 0.5),
                _ev("chromium.i1", "Playing", "5000000", "Artist A", "Song One", 0.4),
                _ev("chromium.i1", "Playing", "6000000", "Artist A", "Song One", 0.3),
            ],
            "poll": 1.5,
        },
        "expected": [
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist A - Song One", True, "paused"),
            ("Artist A - Song One", False, "playing"),
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
            ("", False, "stopped"),
            ("Artist A - Song One", True, "paused"),
            ("", False, "stopped"),
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
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("", False, "stopped"),
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
            ("", False, "stopped"),
            ("Radio - Live Stream", False, "playing"),
        ],
    },
    "percent_title": {
        "streams": _sc(
            [
                _line(
                    "chromium.i1", "Playing", "1000000", "Artist A", "50% {vol} 100%"
                ),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ("Artist A - 50% {vol} 100%", False, "playing"),
        ],
    },
    "html_title": {
        "streams": _sc(
            [
                _line(
                    "chromium.i1",
                    "Playing",
                    "1000000",
                    "AC/DC",
                    '<Live> & "More"',
                ),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ('AC/DC - <Live> & "More"', False, "playing"),
        ],
    },
    "long_title": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "x" * 60),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ("Artist A - " + "x" * 45 + "…", False, "playing"),
        ],
    },
    "wide_title": {
        "streams": _sc(
            [
                _line("chromium.i1", "Playing", "1000000", "Artist A", "曲" * 30),
            ]
        ),
        "expected": [
            ("", False, "stopped"),
            ("Artist A - " + "曲" * 22 + "…", False, "playing"),
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
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist A - Song Two", False, "playing"),
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
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist A - Song Two", False, "playing"),
        ],
    },
}


def _run_scenario(mode, name, spec):
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
    env["MPRIS_POLL_INTERVAL"] = str(streams.get("poll", 0.15))
    env["MPRIS_STALL_MIN_TIME"] = "0.3"
    env["MPRIS_GRACE_SECONDS"] = "0.4"
    env["FAKE_SCENARIO"] = str(scen)
    env["FAKE_OS_STATE"] = str(state_base / f"state_{name}_os.json")
    env["FAKE_FW_STATE"] = str(state_base / f"state_{name}_fw.json")

    proc = subprocess.Popen(
        [sys.executable, str(_SCRIPT), mode],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    norm = _NORM[mode]
    got = []
    deadline = time.time() + 10
    try:
        while time.time() < deadline:
            raw = _readline(proc.stdout, deadline)
            if raw:
                got.append(norm(raw))
                if len(got) >= len(spec["expected"]):
                    break
            elif proc.poll() is not None:
                break
    finally:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        proc.stdout.close()

    shutil.rmtree(tmpdir, ignore_errors=True)

    exp = spec["expected"]
    ok = got == exp
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {mode}/{name}")
    if not ok:
        print(f"  expected: {exp}")
        print(f"  got     : {got}")
    return ok


def main():
    ok = all(
        _run_scenario(mode, name, spec)
        for mode in MODES
        for name, spec in SCENARIOS.items()
    )
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
