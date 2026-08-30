"""Single-pass /proc indexer. O(N) once, O(1) lookups thereafter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcEntry:
    pid: int
    ppid: int
    comm: str
    cmdline: list[str]
    cwd: str


def _parse_stat_ppid(text: str) -> int:
    """Extract ppid (field 4) from /proc/<pid>/stat.

    The comm field (field 2) is wrapped in parens and may itself contain
    parens or spaces, so we cannot use text.split(). The last ')' in the
    line reliably terminates comm; everything after it is space-separated
    single tokens.
    """
    end = text.rindex(")")
    after = text[end + 1 :].split()
    # after = [state, ppid, pgrp, ...]  -> ppid is index 1
    return int(after[1])


class ProcCache:
    """Snapshot of /proc at a point in time."""

    def __init__(self) -> None:
        self._entries: dict[int, ProcEntry] = {}
        self._by_comm: dict[str, set[int]] = {}
        self._by_cmdline_name: dict[str, set[int]] = {}
        self._children: dict[int, set[int]] = {}

    @classmethod
    def snapshot(cls) -> ProcCache:
        """Take a single-pass snapshot of all processes."""
        cache = cls()
        proc_dir = Path("/proc")

        for entry in proc_dir.iterdir():
            if not entry.name.isdigit():
                continue

            pid = int(entry.name)
            try:
                comm = (
                    (entry / "comm")
                    .read_text(encoding="utf-8", errors="replace")
                    .strip()
                )
                cmdline_raw = (entry / "cmdline").read_bytes()
                cmdline = [
                    p.decode(errors="surrogateescape")
                    for p in cmdline_raw.split(b"\0")
                    if p
                ]
                ppid = _parse_stat_ppid((entry / "stat").read_text())
                cwd = os.readlink(str(entry / "cwd"))
            except (OSError, ValueError, IndexError):
                continue

            proc_entry = ProcEntry(
                pid=pid, ppid=ppid, comm=comm, cmdline=cmdline, cwd=cwd
            )
            cache._entries[pid] = proc_entry

            # Index by comm
            cache._by_comm.setdefault(comm.lower(), set()).add(pid)

            # Index by cmdline executable name
            if cmdline:
                exe_name = Path(cmdline[0]).name.lower()
                cache._by_cmdline_name.setdefault(exe_name, set()).add(pid)

            # Build children map
            cache._children.setdefault(ppid, set()).add(pid)

        return cache

    def get(self, pid: int) -> ProcEntry | None:
        return self._entries.get(pid)

    def by_comm(self, name: str) -> set[int]:
        return self._by_comm.get(name.lower(), set())

    def by_cmdline_name(self, name: str) -> set[int]:
        return self._by_cmdline_name.get(name.lower(), set())

    def children(self, pid: int) -> set[int]:
        return self._children.get(pid, set())

    def descendants(self, pid: int) -> set[int]:
        result: set[int] = {pid}
        stack = list(self.children(pid))
        while stack:
            child = stack.pop()
            if child not in result:
                result.add(child)
                stack.extend(self.children(child))
        return result

    def process_named_running(self, name: str) -> bool:
        return bool(self.by_comm(name) or self.by_cmdline_name(name))

    def get_nvim_pid(self, pid: int) -> int | None:
        for child in sorted(self.children(pid)):
            entry = self.get(child)
            if entry and entry.comm == "nvim":
                return child
            deeper = self.get_nvim_pid(child)
            if deeper:
                return deeper
        return None

    def get_zellij_session(self, pid: int) -> str | None:
        for child in sorted(self.children(pid)):
            entry = self.get(child)
            if entry and entry.comm == "zellij":
                # Look for --session or -s <name> or attach -c <name>
                for i, arg in enumerate(entry.cmdline):
                    if arg in ("--session", "-s", "--session-name") and i + 1 < len(
                        entry.cmdline
                    ):
                        return entry.cmdline[i + 1]
                    if arg in ("attach", "a") and "-c" in entry.cmdline:
                        try:
                            idx = entry.cmdline.index("-c")
                            if idx + 1 < len(entry.cmdline):
                                return entry.cmdline[idx + 1]
                        except ValueError:
                            pass
                return entry.cmdline[0] if entry.cmdline else "zellij"
            deeper = self.get_zellij_session(child)
            if deeper:
                return deeper
        return None

    def get_foot_cwd(self, pid: int) -> str:
        home = str(Path.home())
        cwd = home
        for child in sorted(self.children(pid)):
            entry = self.get(child)
            if entry and entry.comm in (
                "bash",
                "zsh",
                "fish",
                "sh",
                "dash",
                "nu",
                "zellij",
            ):
                cwd = entry.cwd
        nvim_pid = self.get_nvim_pid(pid)
        if nvim_pid is not None and cwd == home:
            nvim_entry = self.get(nvim_pid)
            if nvim_entry:
                cwd = nvim_entry.cwd
        # For zellij, cwd is the shell inside zellij, not zellij itself
        zellij_sess = self.get_zellij_session(pid)
        if zellij_sess is not None and cwd == home:
            for child in self.descendants(pid):
                entry = self.get(child)
                if entry and entry.comm in ("bash", "zsh", "fish"):
                    cwd = entry.cwd
                    break
        return cwd

    def is_ssh_or_sudo(self, pid: int) -> tuple[bool, str]:
        for child in self.descendants(pid):
            entry = self.get(child)
            if not entry:
                continue
            if entry.comm in ("ssh", "sudo", "su", "doas"):
                return True, " ".join(entry.cmdline[:3])
            # Also check cmdline name for ssh wrapped in bash -c
            if entry.cmdline and Path(entry.cmdline[0]).name in ("ssh", "sudo"):
                return True, " ".join(entry.cmdline[:3])
        return False, ""
