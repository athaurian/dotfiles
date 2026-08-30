"""Tests for the save-side tree serialization (clean_tree)."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import session_manager_lib.sway_tree as st_mod
from session_manager_lib.tests.helpers import make_window


def tree_window(app_id, **extra):
    """A window as it appears in a LIVE sway tree (type 'con')."""
    win = make_window(app_id)
    win["type"] = "con"
    win["floating_nodes"] = []
    win["nodes"] = []
    win.update(extra)
    return win


class FakeCache:
    def __init__(self, cwd="/home/user/proj", nvim_pid=None):
        self.cwd = cwd
        self.nvim_pid = nvim_pid

    def get_foot_cwd(self, pid):
        return self.cwd

    def get_nvim_pid(self, pid):
        return self.nvim_pid

    def get_zellij_session(self, pid):
        return None

    def is_ssh_or_sudo(self, pid):
        return False, ""


class CleanTreeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patches = [
            unittest.mock.patch.object(
                st_mod,
                "get_nvim_snapshot_path",
                lambda cwd, pid: Path(self.tmp.name) / f"snap_{pid}.vim",
            ),
            unittest.mock.patch.object(
                st_mod,
                "snacks_sidecar_path",
                lambda p: Path(str(p) + ".snacks"),
            ),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])


class TestCleanTreeWindows(CleanTreeTestCase):
    def test_foot_without_nvim(self):
        node = tree_window("foot", name="foot", pid=10)
        result = st_mod.clean_tree(node, FakeCache(cwd="/home/user/proj"))
        self.assertEqual(result["type"], "window")
        self.assertEqual(result["app_id"], "foot")
        self.assertEqual(result["nvim_type"], "none")
        self.assertEqual(result["cwd"], "/home/user/proj")
        self.assertEqual(result["name"], "foot")

    def test_foot_restored_app_id_normalised(self):
        node = tree_window("foot_restored_abc", name="foot", pid=10)
        result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["app_id"], "foot")

    def test_foot_dashboard_nvim(self):
        with unittest.mock.patch.object(
            st_mod,
            "get_foot_nvim_state",
            return_value=(77, {"buffers": [], "windows": []}),
        ):
            node = tree_window("foot", name="foot", pid=10)
            result = st_mod.clean_tree(
                node, FakeCache(cwd="/home/user/proj", nvim_pid=77)
            )
        self.assertEqual(result["nvim_type"], "dashboard")

    def test_foot_session_nvim(self):
        snap = Path(self.tmp.name) / "snap_77.vim"
        snap.write_text("vim session", encoding="utf-8")
        with (
            unittest.mock.patch.object(
                st_mod,
                "get_foot_nvim_state",
                return_value=(77, {"buffers": [{"name": "/x", "buftype": ""}]}),
            ),
            unittest.mock.patch.object(
                st_mod, "create_manager_snapshot", return_value=(True, None)
            ),
        ):
            node = tree_window("foot", name="foot", pid=10)
            result = st_mod.clean_tree(
                node, FakeCache(cwd="/home/user/proj", nvim_pid=77)
            )
        self.assertEqual(result["nvim_type"], "session")
        self.assertTrue(result["nvim_snapshot"].endswith("snap_77.vim"))
        self.assertNotIn("nvim_snacks_sidecar", result)

    def test_zathura_window(self):
        with unittest.mock.patch.object(
            st_mod, "get_zathura_info", return_value=("/docs/x.pdf", 3)
        ):
            node = tree_window("org.pwmt.zathura", pid=10)
            result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["document_path"], "/docs/x.pdf")
        self.assertEqual(result["page_number"], 3)

    def test_calibre_viewer_window(self):
        with (
            unittest.mock.patch.object(
                st_mod,
                "calibre_title_from_window",
                return_value=("My Book", "EPUB"),
            ),
            unittest.mock.patch.object(
                st_mod, "get_ebook_viewer_document", return_value="/books/my.epub"
            ),
        ):
            node = tree_window(
                "calibre-ebook-viewer", name="My Book [EPUB] — E-book viewer"
            )
            result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["document_path"], "/books/my.epub")
        self.assertEqual(result["calibre_format"], "EPUB")

    def test_generic_window_passthrough(self):
        node = tree_window("vesktop", name="Discord", fullscreen_mode=1, marks=["m1"])
        result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["app_id"], "vesktop")
        self.assertEqual(result["fullscreen_mode"], 1)
        self.assertEqual(result["marks"], ["m1"])
        self.assertEqual(result["rect"]["width"], 800)
        self.assertNotIn("cwd", result)


class TestCleanTreeStructure(CleanTreeTestCase):
    def test_empty_con_returns_none(self):
        self.assertIsNone(
            st_mod.clean_tree(
                {"type": "con", "nodes": [], "floating_nodes": []}, FakeCache()
            )
        )

    def test_workspace_keeps_children_and_layout(self):
        win = tree_window("foot", name="foot", pid=10)
        ws = {
            "type": "workspace",
            "layout": "tabbed",
            "nodes": [win],
            "floating_nodes": [],
        }
        result = st_mod.clean_tree(ws, FakeCache())
        self.assertEqual(result["type"], "workspace")
        self.assertEqual(result["layout"], "tabbed")
        self.assertEqual(len(result["nodes"]), 1)
        self.assertNotIn("name", result)  # save.py adds the name afterwards

    def test_workspace_filters_empty_children(self):
        ws = {
            "type": "workspace",
            "layout": "splith",
            "nodes": [
                {"type": "con", "nodes": [], "floating_nodes": []},
                tree_window("foot", name="foot", pid=10),
            ],
            "floating_nodes": [],
        }
        result = st_mod.clean_tree(ws, FakeCache())
        self.assertEqual(len(result["nodes"]), 1)

    def test_scratchpad_state_preserved(self):
        node = tree_window("foot", name="foot", pid=10, scratchpad_state="shown")
        result = st_mod.clean_tree(node, FakeCache())
        self.assertEqual(result["scratchpad_state"], "shown")


if __name__ == "__main__":
    unittest.main()
