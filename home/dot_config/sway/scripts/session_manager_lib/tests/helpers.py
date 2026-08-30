"""Shared helpers for the session manager test suite.

All tests run against the chezmoi source tree (PYTHONPATH) and never touch a
live sway instance or launch processes. Live IPC / app launches are replaced
by recording fakes.
"""

import unittest


def make_window(app_id="foot", **extra):
    node = {
        "type": "window",
        "app_id": app_id,
        "class": "",
        "name": f"{app_id} window",
        "pid": 12345,
        "fullscreen_mode": 0,
        "rect": {"x": 0, "y": 0, "width": 800, "height": 600},
        "marks": [],
        "scratchpad_state": "none",
    }
    node.update(extra)
    return node


def make_con(nodes=None, floating=None, layout="splith"):
    return {
        "type": "con",
        "layout": layout,
        "nodes": nodes or [],
        "floating_nodes": floating or [],
    }


def make_workspace(name, nodes=None, floating=None, layout="splith"):
    ws = make_con(nodes, floating, layout)
    ws["type"] = "workspace"
    ws["name"] = name
    return ws


class RestoreHarnessTestCase(unittest.TestCase):
    """Base class: patches the restore module's IPC/launch/notify entry
    points with recorders so `_restore_*` helpers can run hermetically."""

    def setUp(self):
        import unittest.mock

        import session_manager_lib.restore as restore_mod

        self.restore_mod = restore_mod
        self.calls: list[str] = []
        self._id_iter = iter(range(1000, 200000))
        self._patches = [
            unittest.mock.patch.object(restore_mod, "cmd", self._record_cmd),
            unittest.mock.patch.object(restore_mod, "run_command", self._record_cmd),
            unittest.mock.patch.object(restore_mod, "get_tree", self._fake_get_tree),
            unittest.mock.patch.object(
                restore_mod, "launch_and_get_id", self._fake_launch
            ),
            unittest.mock.patch.object(
                restore_mod, "get_helium_restored_id", self._fake_helium_id
            ),
            unittest.mock.patch.object(restore_mod, "notify", lambda *a, **kw: None),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _record_cmd(self, cmd):
        self.calls.append(cmd)
        return True

    def _fake_get_tree(self):
        # Single active output; mirrors the 1920x1080 default clamp box in
        # _clamp_rect_to_output so geometry assertions stay unchanged.
        return {
            "nodes": [
                {
                    "type": "output",
                    "name": "HEADLESS-1",
                    "active": True,
                    "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                }
            ],
            "floating_nodes": [],
        }

    def _fake_launch(self, node, claimed_ids):
        win_id = next(self._id_iter)
        claimed_ids.add(win_id)
        return win_id

    def _fake_helium_id(self, node, ctx):
        idx = ctx.helium_saved_index.get(id(node))
        if idx is None:
            return None
        if ctx.helium_restored_ids[idx] is None:
            ctx.helium_restored_ids[idx] = next(self._id_iter)
        return ctx.helium_restored_ids[idx]

    def restore_workspaces(self, payload):
        from session_manager_lib.apps.helium import collect_helium_nodes
        from session_manager_lib.restore import _normalise_restore_payload

        workspaces, scratchpad, _bg, _focused = _normalise_restore_payload(payload)
        ctx = self.restore_mod.RestoreContext()
        for ws in workspaces:
            collect_helium_nodes(ws, ctx)
        for node in scratchpad:
            collect_helium_nodes(node, ctx)
        for ws in workspaces:
            self.restore_mod._restore_node(ws, ctx)
        for node in scratchpad:
            self.restore_mod._restore_hidden_scratchpad(node, ctx)
        return ctx

    def assertCommand(self, needle, msg=None):
        self.assertTrue(
            any(needle in c for c in self.calls),
            msg or f"no command contains {needle!r}; got: {self.calls}",
        )
