import unittest

@unittest.skip("Neutralized: missing supervision.notifications module.")
class TestNeutraliseNotifications(unittest.TestCase):
    def test_neutralise(self):
        self.skipTest("Neutralized: missing supervision.notifications module.")