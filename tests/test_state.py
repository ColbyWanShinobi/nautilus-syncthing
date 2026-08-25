import unittest

from nautilus_syncthing.state import StateService


class StateTests(unittest.TestCase):
    def test_transfer_events_are_applied_and_finished(self):
        active = StateService._apply_events(set(), [{"type": "ItemStarted", "data": {"folder": "docs", "item": "a.txt"}}])
        self.assertEqual(active, {("docs", "a.txt")})
        active = StateService._apply_events(active, [{"type": "ItemFinished", "data": {"folder": "docs", "item": "a.txt"}}])
        self.assertEqual(active, set())
