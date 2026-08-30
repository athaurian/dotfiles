#!/usr/bin/env python3
"""Integration tests for the Waybar MPRIS module.

Runs executable_mpris.py against a fake playerctl that replays canned
scenarios simulating Chromium-family quirks. Each scenario asserts the
exact sequence of emitted Waybar payloads.

Run from the repository root::

    python3 home/dot_config/waybar/scripts/tests/test_mpris.py

Or via::

    make check-mpris
"""

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "executable_mpris.py"
_FAKE_BIN = _HERE  # fake_playerctl.py lives here; rename to "playerctl" on PATH
_F = "\x1f"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _line(player, status, pos, artist, title):
    return _F.join((player, status, pos, artist, title))


def _norm(text):
    """Extract (label, italic) from a Waybar payload for assertion."""
    t = re.sub(r"<span>[^<]*</span>", "", text)
    italic = "<i>" in t
    t = re.sub(r"</?i>", "", t).strip()
    return t, italic


def _sc(events, delay=0.15):
    """Wrap a list of lines/exit-events into oneshot+follow streams."""
    os_ev = [e if isinstance(e, dict) else {"line": e} for e in events]
    fw_ev = [e if isinstance(e, dict) else {"line": e, "delay": delay} for e in events]
    return {"oneshot": os_ev, "follow": fw_ev}


def _make_fakebin():
    """Create a temp dir with a 'playerctl' symlink pointing to fake_playerctl.py."""
    tmpdir = Path(tempfile.mkdtemp(prefix="mpris_fake_"))
    fakebin = tmpdir / "bin"
    fakebin.mkdir()
    link = fakebin / "playerctl"
    link.symlink_to(_HERE / "fake_playerctl.py")
    link.chmod(0o755)
    return tmpdir, fakebin


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS = {
    # 1. Track change: Chromium publishes empty Metadata mid-transition.
    #    Cache keeps Song One visible through the gap, then shows Song Two.
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
    # 2. Stale PlaybackStatus: Chromium says Playing but position frozen.
    #    Must downgrade to Paused, then recover to Playing on resume.
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
            ("", False, "stopped"),
            ("Artist A - Song One", False, "playing"),
            ("Artist A - Song One", True, "paused"),
            ("Artist A - Song One", False, "playing"),
        ],
    },
    # 3. Long pause: metadata cleared while Paused. Song must stay visible
    #    through the grace window, then disappear after an explicit Stopped.
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
    # 4. Player disappears (playerctl exits non-zero), a different instance
    #    appears with empty metadata. Must show blank, no cache leakage.
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
    # 5. Live stream: position is 0. Must stay Playing, never downgrade
    #    to Paused via stall detection.
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
    # 6. Chromium blips a Stopped reading mid track-change. Grace keeps the
    #    song visible through the blink, then the new track appears.
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
    # 7. Follow goes silent (playerctl issue #288: stops emitting after the
    #    player churns). The resync poll must recover the new track.
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


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


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
                obj = json.loads(raw)
                label, italic = _norm(obj["text"])
                got.append((label, italic, obj["class"]))
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

    import shutil

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
