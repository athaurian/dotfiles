#!/usr/bin/env python3
"""Fake playerctl for test harness.

Serves one-shot metadata queries and --follow streams from scenario files.
Scenario files are JSON with ``{"oneshot": [...], "follow": [...]}`` keys.
Each entry is a dict like ``{"line": "..."}``, ``{"line": "...", "delay": 0.15}``,
or ``{"exit": 1}``.
"""

import json
import os
import sys
import time

with open(os.environ["FAKE_SCENARIO"]) as _f:
    scenario = json.load(_f)
is_follow = "--follow" in sys.argv

if is_follow:
    state_file = os.environ["FAKE_FW_STATE"]
    stream = scenario.get("follow", [])
else:
    state_file = os.environ["FAKE_OS_STATE"]
    stream = scenario.get("oneshot", [])

idx = 0
try:
    with open(state_file) as _f:
        idx = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    pass


def advance(i):
    with open(state_file, "w") as f:
        json.dump(i, f)


def norm(ev):
    return ev if isinstance(ev, dict) else {"line": ev}


if not is_follow:
    if idx < len(stream):
        advance(idx + 1)
        ev = norm(stream[idx])
    else:
        ev = norm(stream[-1]) if stream else {"exit": 1}
    if "exit" in ev:
        sys.exit(ev["exit"])
    sys.stdout.write(ev["line"] + "\n")
    sys.stdout.flush()
    sys.exit(0)

# Follow mode: emit remaining events with pacing, then sleep to stay alive.
for j in range(idx, len(stream)):
    ev = norm(stream[j])
    time.sleep(ev.get("delay", 0.0))
    if "exit" in ev:
        advance(j + 1)
        sys.exit(ev["exit"])
    sys.stdout.write(ev["line"] + "\n")
    sys.stdout.flush()
    advance(j + 1)

time.sleep(30)
