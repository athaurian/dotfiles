"""Tests for the /proc snapshot machinery."""

import unittest

from session_manager_lib.proc_cache import ProcCache, ProcEntry, _parse_stat_ppid


class TestParseStatPpid(unittest.TestCase):
    def test_simple_comm(self):
        self.assertEqual(_parse_stat_ppid("1234 (bash) S 42 1234 1234 0"), 42)

    def test_comm_with_spaces(self):
        self.assertEqual(_parse_stat_ppid("99 (my proc with spaces) S 7 99 99 0"), 7)

    def test_comm_with_parens(self):
        self.assertEqual(_parse_stat_ppid("5 (a(b)c)) S 13 5 5 0"), 13)

    def test_comm_with_closing_paren_only(self):
        self.assertEqual(_parse_stat_ppid("6 (foo)bar) S 8 6 6 0"), 8)

    def test_multi_digit_ppid(self):
        self.assertEqual(
            _parse_stat_ppid("100 (bash) S 123456 100 100 34816 0"), 123456
        )


class TestProcCache(unittest.TestCase):
    def _inject(self, cache, pid, ppid, comm, cmdline=None, cwd="/"):
        cache._entries[pid] = ProcEntry(
            pid=pid,
            ppid=ppid,
            comm=comm,
            cmdline=cmdline or [],
            cwd=cwd,
        )
        cache._by_comm.setdefault(comm.lower(), set()).add(pid)
        if cmdline:
            from pathlib import Path

            cache._by_cmdline_name.setdefault(Path(cmdline[0]).name.lower(), set()).add(
                pid
            )
        cache._children.setdefault(ppid, set()).add(pid)

    def test_children_and_descendants(self):
        cache = ProcCache()
        self._inject(cache, 1, 0, "root")
        self._inject(cache, 2, 1, "shell")
        self._inject(cache, 3, 2, "child")
        self._inject(cache, 4, 2, "other")
        self.assertEqual(cache.children(1), {2})
        self.assertEqual(cache.descendants(1), {1, 2, 3, 4})
        self.assertEqual(cache.descendants(2), {2, 3, 4})
        self.assertEqual(cache.descendants(3), {3})

    def test_by_comm_is_case_insensitive(self):
        cache = ProcCache()
        self._inject(cache, 9, 0, "NVIM")
        self.assertEqual(cache.by_comm("nvim"), {9})
        self.assertEqual(cache.by_comm("NVIM"), {9})
        self.assertTrue(cache.process_named_running("nvim"))
        self.assertFalse(cache.process_named_running("absent"))

    def test_by_cmdline_name(self):
        cache = ProcCache()
        self._inject(cache, 11, 0, "prog", cmdline=["/usr/bin/prog", "--flag"])
        self.assertEqual(cache.by_cmdline_name("prog"), {11})
        self.assertTrue(cache.process_named_running("prog"))

    def test_get_missing(self):
        self.assertIsNone(ProcCache().get(999999))

    def test_get_nvim_pid_recursive(self):
        cache = ProcCache()
        self._inject(cache, 1, 0, "foot")
        self._inject(cache, 2, 1, "bash")
        self._inject(cache, 3, 2, "nvim")
        self.assertEqual(cache.get_nvim_pid(1), 3)

    def test_get_foot_cwd_prefers_shell_child(self):
        cache = ProcCache()
        self._inject(cache, 1, 0, "foot")
        self._inject(cache, 2, 1, "bash", cwd="/work")
        self._inject(cache, 3, 1, "nvim", cwd="/elsewhere")
        self.assertEqual(cache.get_foot_cwd(1), "/work")

    def test_get_foot_cwd_deterministic_with_multiple_shells(self):
        cache = ProcCache()
        self._inject(cache, 1, 0, "foot")
        self._inject(cache, 2, 1, "zsh", cwd="/first")
        self._inject(cache, 3, 1, "bash", cwd="/second")
        # Sorted iteration ensures last pid wins deterministically.
        self.assertEqual(cache.get_foot_cwd(1), "/second")


if __name__ == "__main__":
    unittest.main()
