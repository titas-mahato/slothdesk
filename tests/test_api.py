"""
Integration and API tests for SlothDesk FastAPI endpoints.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (
    health_check,
    get_drawers,
    get_sandbox_default,
    messify_sandbox,
    tidy_sandbox,
)


class TestSlothDeskAPI(unittest.TestCase):

    def test_health_endpoint(self):
        h = health_check()
        self.assertEqual(h["status"], "ok")
        self.assertEqual(h["app"], "SlothDesk")
        self.assertEqual(h["sloth_status"], "happily_napping")

    def test_get_drawers_metadata(self):
        drawers = get_drawers()
        self.assertIn("Finance & Receipts", drawers)
        self.assertIn("Development & Tech", drawers)
        self.assertIn("Media & Screenshots", drawers)
        self.assertIn("Documents & Reference", drawers)
        self.assertIn("Installers & Archives", drawers)

    def test_get_default_sandbox_files(self):
        defaults = get_sandbox_default()
        self.assertTrue(len(defaults) >= 5)

    def test_messify_sandbox(self):
        scrambled = messify_sandbox()
        self.assertTrue(len(scrambled) >= 5)

    def test_tidy_sandbox(self):
        plan = tidy_sandbox(None)
        self.assertTrue(plan.total_files >= 5)
        self.assertTrue(plan.metrics.laziness_score > 50)
        self.assertIn("Finance & Receipts", plan.drawers)


if __name__ == "__main__":
    unittest.main()
