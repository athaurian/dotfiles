"""Tests for the Sway IPC tree helpers."""

import unittest

from session_manager_lib.ipc import (
    is_window_node,
    matches_app,
    matching_window_ids_in_tree,
    node_class,
    walk_tree,
)


def node(nid, **extra):
    n = {"id": nid, "type": "con", "nodes": [], "floating_nodes": []}
    if "cls" in extra:
        n["class"] = extra.pop("cls")
    n.update(extra)
    return n


def win(nid, app_id=None, cls=None):
    n = node(nid, type="con", app_id=app_id)
    if cls:
        n["window_properties"] = {"class": cls}
    return n


class TestWalkTree(unittest.TestCase):
    def test_dfs_order_including_floating(self):
        tree = node(
            1,
            nodes=[node(2, nodes=[node(3)])],
            floating_nodes=[node(4, floating_nodes=[node(5)])],
        )
        self.assertEqual([n["id"] for n in walk_tree(tree)], [1, 2, 3, 4, 5])

    def test_empty_tree(self):
        self.assertEqual(list(walk_tree({})), [{}])


class TestNodeClass(unittest.TestCase):
    def test_window_properties_preferred(self):
        n = node(1, window_properties={"class": "X"}, cls="Y")
        self.assertEqual(node_class(n), "X")

    def test_falls_back_to_class(self):
        self.assertEqual(node_class(node(1, cls="Y")), "Y")

    def test_empty(self):
        self.assertEqual(node_class(node(1)), "")


class TestMatchesApp(unittest.TestCase):
    def test_app_id_exact(self):
        self.assertTrue(matches_app(win(1, app_id="foot"), "foot", ""))
        self.assertFalse(matches_app(win(1, app_id="foot"), "vesktop", ""))

    def test_app_id_prefers_app_id_over_class(self):
        self.assertFalse(matches_app(win(1, app_id="foot"), "", "Foot"))

    def test_x11_class_match(self):
        self.assertTrue(matches_app(win(1, cls="thunar"), "", "thunar"))
        self.assertFalse(matches_app(win(1, cls="thunar"), "", "nemo"))

    def test_x11_class_when_app_id_requested(self):
        self.assertTrue(matches_app(win(1, cls="thunar"), "thunar", "thunar"))
        self.assertFalse(matches_app(win(1, cls="thunar"), "foot", ""))


class TestIsWindowNode(unittest.TestCase):
    def test_wayland_window(self):
        self.assertTrue(is_window_node(win(1, app_id="foot")))

    def test_x11_window_via_properties(self):
        self.assertTrue(is_window_node(win(1, cls="thunar")))

    def test_container_not_window(self):
        self.assertFalse(is_window_node(node(1)))

    def test_workspace_not_window(self):
        self.assertFalse(is_window_node(node(1, type="workspace")))


class TestMatchingWindowIds(unittest.TestCase):
    def test_matches_app_and_returns_ids(self):
        tree = node(
            1,
            nodes=[
                win(2, app_id="foot"),
                win(3, app_id="vesktop"),
                node(4, nodes=[win(5, app_id="foot")]),
            ],
        )
        self.assertEqual(matching_window_ids_in_tree(tree, "foot", ""), [2, 5])

    def test_no_matches(self):
        tree = node(1, nodes=[win(2, app_id="foot")])
        self.assertEqual(matching_window_ids_in_tree(tree, "nope", ""), [])


if __name__ == "__main__":
    unittest.main()
