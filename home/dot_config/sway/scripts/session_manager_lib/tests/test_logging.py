"""Tests for desktop notification delivery."""

import unittest
import unittest.mock

from session_manager_lib import logging_setup


class NotifyTestCase(unittest.TestCase):
    def setUp(self):
        self.last_id = unittest.mock.patch.object(
            logging_setup, "_last_notify_id", None
        )
        self.last_id.start()
        self.addCleanup(self.last_id.stop)
        self.missing = unittest.mock.patch.object(
            logging_setup, "_notify_send_missing", False
        )
        self.missing.start()
        self.addCleanup(self.missing.stop)

    def patch_run(self, **kwargs):
        run = unittest.mock.patch.object(logging_setup.subprocess, "run", **kwargs)
        self.run = run.start()
        self.addCleanup(run.stop)
        return self.run


class TestNotify(NotifyTestCase):
    def test_sends_the_message_and_options(self):
        run = self.patch_run(return_value=unittest.mock.Mock(stdout="42\n"))
        logging_setup.notify("hello", timeout_ms=5000, urgency="normal")
        command = run.call_args.args[0]
        self.assertIn("hello", command)
        self.assertIn("normal", command)
        self.assertIn("5000", command)
        self.assertNotIn("-r", command)

    def test_replaces_the_previous_notification(self):
        run = self.patch_run(return_value=unittest.mock.Mock(stdout="42\n"))
        logging_setup.notify("first")
        logging_setup.notify("second")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-r") + 1], "42")

    def test_invalid_reply_id_is_not_reused(self):
        run = self.patch_run(return_value=unittest.mock.Mock(stdout="not-a-number\n"))
        logging_setup.notify("first")
        logging_setup.notify("second")
        self.assertNotIn("-r", run.call_args.args[0])

    def test_missing_notify_send_disables_further_calls(self):
        run = self.patch_run(side_effect=FileNotFoundError)
        logging_setup.notify("first")
        logging_setup.notify("second")
        self.assertEqual(run.call_count, 1)

    def test_other_delivery_errors_do_not_raise(self):
        self.patch_run(side_effect=OSError("dbus gone"))
        logging_setup.notify("hello")


if __name__ == "__main__":
    unittest.main()
