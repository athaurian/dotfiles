"""Cliphist backend: lists entries, decodes selections, copies results."""

from __future__ import annotations

import shutil
import subprocess

from picker_lib import model
from picker_lib.backend import EntryNotFoundError


class CliphistBackend:
    """Wayland clipboard history backed by cliphist and wl-clipboard."""

    name = "cliphist"

    def available(self) -> bool:
        """Checks whether the cliphist binary is available."""
        return shutil.which("cliphist") is not None

    def _base_args(self, db_path: str | None) -> list[str]:
        args = ["cliphist"]
        if db_path is not None:
            args += ["-db-path", db_path]
        return args

    def list_entries(self, db_path: str | None = None) -> list[tuple[int, str]]:
        """Lists clipboard history as id and display pairs, newest first.

        Malformed lines are skipped. Raises FileNotFoundError when
        cliphist is missing and RuntimeError when listing fails.
        """
        try:
            result = subprocess.run(
                self._base_args(db_path) + ["list"],
                check=False,
                capture_output=True,
                text=True,
                # Previews may carry arbitrary bytes. Skip one bad entry
                # instead of failing the whole listing. Ids are ASCII and survive.
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("cliphist not installed") from exc
        if result.returncode != 0:
            # A missing database means nothing was stored yet, so an empty
            # history is not an error. This is cliphist's own wording.
            if "please store something first" in result.stderr:
                return []
            raise RuntimeError(f"cliphist list failed: {result.stderr.strip()}")
        entries = []
        for line in result.stdout.splitlines():
            eid, display = model.split_entry(line)
            if eid is None:
                continue
            entries.append((eid, display))
        return entries

    def decode(self, payload: bytes, db_path: str | None = None) -> bytes:
        """Decodes a cliphist selection from a full menu line or bare id
        to raw bytes.

        The payload must not end with a newline. Cliphist rejects bare ids
        with a trailing newline, so callers pass exact bytes.

        Raises:
            FileNotFoundError: When cliphist is not installed.
            EntryNotFoundError: When the entry vanished after listing.
            RuntimeError: When decoding fails for another reason.
        """
        try:
            result = subprocess.run(
                self._base_args(db_path) + ["decode"],
                input=payload,
                check=False,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("cliphist not installed") from exc
        if result.returncode != 0:
            err = result.stderr.decode()
            # The entry rotated out of the history after listing.
            if "not found" in err:
                raise EntryNotFoundError(err.strip())
            raise RuntimeError(f"cliphist decode failed: {err!r}")
        return result.stdout

    def copy_to_clipboard(self, data: bytes) -> None:
        """Copies raw bytes to the Wayland clipboard with MIME type
        auto-detected.

        Raises FileNotFoundError when wl-copy is missing and RuntimeError
        when copying fails.
        """
        try:
            # wl-copy forks a clipboard daemon that inherits the pipes, so
            # capturing its output hangs until that daemon exits.
            result = subprocess.run(
                ["wl-copy"],
                input=data,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError("wl-copy not installed") from exc
        if result.returncode != 0:
            raise RuntimeError(f"wl-copy failed with status {result.returncode}")
