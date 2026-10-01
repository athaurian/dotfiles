#!/usr/bin/env python3
# Runs a `playerctl --follow` stream and a periodic poll through one
# state machine. Chromium sends event bursts that the follow stream
# misses or merges, and it recycles players in ways that can silence
# the stream. Follow-only then loses state, while poll-only reacts
# late. The polybar twin of this script emits format tags instead of
# JSON. Apply any change to the event model to both files.

import html
import json
import os
import queue
import subprocess
import sys
import threading
import time
import unicodedata
from functools import lru_cache

ICON_PLAYING = "󰐊"
ICON_PAUSED = "󰏤"

MAX_TEXT_LEN = 56

POLL_INTERVAL = float(os.environ.get("MPRIS_POLL_INTERVAL", "1.0"))

STALL_DETECTION = True
STALL_MIN_TIME = float(os.environ.get("MPRIS_STALL_MIN_TIME", "1.0"))
STALL_POLLS = int(os.environ.get("MPRIS_STALL_POLLS", "1"))

GRACE_SECONDS = float(os.environ.get("MPRIS_GRACE_SECONDS", "2.0"))

_EMPTY_PAYLOAD: str = json.dumps({"text": "", "class": "stopped", "alt": "stopped"})
_SPAN_PLAYING: str = f"<span>{ICON_PLAYING}</span>"
_SPAN_PAUSED: str = f"<span>{ICON_PAUSED}</span>"

_FIELD_SEP = "\x1f"


@lru_cache(maxsize=2048)
def _char_width(ch: str) -> int:
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1


def _truncate(label: str, limit: int = MAX_TEXT_LEN) -> str:
    width = 0
    for i, ch in enumerate(label):
        width += _char_width(ch)
        if width > limit:
            return label[:i] + "…"
    return label


def _emit(payload: str) -> None:
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()


def _parse_position(pos: str) -> int | None:
    try:
        value = int(pos.strip())
    except (AttributeError, ValueError):
        return None
    return value if value > 0 else None


def _playerctl_cmd(follow: bool) -> list[str]:
    cmd = ["playerctl", "--player=%any", "metadata"]
    if follow:
        cmd.append("--follow")
    cmd.extend(
        [
            "--format",
            _FIELD_SEP.join(
                (
                    "{{playerName}}",
                    "{{status}}",
                    "{{position}}",
                    "{{artist}}",
                    "{{title}}",
                )
            ),
        ]
    )
    return cmd


def _split_fields(line: str) -> tuple[str, str, str, str, str] | None:
    line = line.strip()
    if not line:
        return None
    fields = line.split(_FIELD_SEP, 4)
    player = fields[0].strip() if len(fields) > 0 else ""
    status = fields[1].strip() if len(fields) > 1 else ""
    position = fields[2].strip() if len(fields) > 2 else ""
    artist = fields[3].strip() if len(fields) > 3 else ""
    title = fields[4].strip() if len(fields) > 4 else ""
    return player, status, position, artist, title


def _query_player() -> tuple[str, str, str, str, str] | None:
    try:
        proc = subprocess.run(
            _playerctl_cmd(follow=False),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        _emit(_EMPTY_PAYLOAD)
        sys.exit(0)
    except subprocess.TimeoutExpired:
        return None

    if proc.returncode != 0 or not proc.stdout.strip():
        return "", "", "", "", ""
    return _split_fields(proc.stdout)


def _render(status: str, artist: str, title: str) -> str:
    span = _SPAN_PLAYING if status == "Playing" else _SPAN_PAUSED

    if artist and title:
        label = f"{artist} - {title}"
    elif title:
        label = title
    elif artist:
        label = artist
    else:
        return _EMPTY_PAYLOAD

    label = _truncate(label)
    label = html.escape(label, quote=False)
    text = f"{span}  {label}"

    if status == "Paused":
        text = f"<i>{text}</i>"

    return json.dumps({"text": text, "class": status.lower(), "alt": status.lower()})


class _PlayerState:
    def __init__(self) -> None:
        self.cache_artist = ""
        self.cache_title = ""
        self.last_status = ""
        self.last_player = ""
        self.last_pos: int | None = None
        self.last_pos_time: float | None = None
        self.last_active_time: float | None = None
        self.stall = 0
        self.last_payload = _EMPTY_PAYLOAD

    def process(self, fields: tuple[str, str, str, str, str] | None) -> str | None:
        if fields is None:
            return None

        player, status, position, artist, title = fields
        payload = _EMPTY_PAYLOAD

        if status == "Stopped" or not status:
            now = time.monotonic()
            still_grace = (
                self.last_active_time is not None
                and now - self.last_active_time < GRACE_SECONDS
            )
            if still_grace and (self.cache_artist or self.cache_title):
                # Chromium briefly reports an empty or Stopped status during
                # track changes. The cache keeps the song visible for
                # `GRACE_SECONDS`.
                payload = _render(self.last_status, self.cache_artist, self.cache_title)
            else:
                self.cache_artist = self.cache_title = ""
                self.last_status = ""
                self.last_player = ""
                self.last_pos = None
                self.last_pos_time = None
                self.last_active_time = None
                self.stall = 0
        else:
            self.last_active_time = time.monotonic()

            if player != self.last_player:
                self.last_player = player
                self.cache_artist = self.cache_title = ""
                self.last_pos = None
                self.last_pos_time = None
                self.stall = 0

            if artist and title:
                self.cache_artist, self.cache_title = artist, title
            else:
                # Chromium clears its metadata during long pauses and track
                # changes. The cached artist and title fill that gap.
                artist = artist or self.cache_artist
                title = title or self.cache_title

            # Chromium reports Playing while it is paused. A frozen position
            # then renders the state as Paused.
            if STALL_DETECTION and status == "Playing":
                pos = _parse_position(position)
                now = time.monotonic()
                if pos is not None:
                    if pos == self.last_pos and self.last_pos_time is not None:
                        if now - self.last_pos_time >= STALL_MIN_TIME:
                            self.stall += 1
                            if self.stall >= STALL_POLLS:
                                status = "Paused"
                    else:
                        self.stall = 0
                        self.last_pos = pos
                        self.last_pos_time = now
                else:
                    self.stall = 0
                    self.last_pos = None
                    self.last_pos_time = None
            else:
                self.stall = 0
                self.last_pos = None
                self.last_pos_time = None

            self.last_status = status
            payload = _render(status, artist, title)

        if payload == self.last_payload:
            return None
        self.last_payload = payload
        return payload


def _follow_reader(proc: subprocess.Popen, events: queue.Queue) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        events.put(("line", line))
    events.put(("eof", None))


def main() -> None:
    state = _PlayerState()
    proc: subprocess.Popen | None = None
    events: queue.Queue = queue.Queue()

    _emit(_EMPTY_PAYLOAD)

    while True:
        if proc is None:
            try:
                proc = subprocess.Popen(
                    _playerctl_cmd(follow=True),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            except FileNotFoundError:
                _emit(_EMPTY_PAYLOAD)
                sys.exit(0)
            threading.Thread(
                target=_follow_reader, args=(proc, events), daemon=True
            ).start()
            continue

        try:
            kind, value = events.get(timeout=POLL_INTERVAL)
        except queue.Empty:
            payload = state.process(_query_player())
            if payload is not None:
                _emit(payload)
            continue

        if kind == "eof":
            if proc is not None:
                try:
                    proc.wait(timeout=2.0)
                except (OSError, subprocess.SubprocessError):
                    pass
            proc = None
            continue

        payload = state.process(_split_fields(value))
        if payload is not None:
            _emit(payload)


if __name__ == "__main__":
    main()
