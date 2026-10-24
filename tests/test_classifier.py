"""
Unit tests for the SlothDesk local semantic classification and smart renaming engine.
"""

import os
import sys
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import DrawerType, FileDescriptor
from app.classifier import SemanticJanitorClassifier
from app.renamer import extract_date, generate_smart_name, sanitize_slug


class TestSlothClassifier(unittest.TestCase):

    def setUp(self):
        self.classifier = SemanticJanitorClassifier()

    def test_financial_statement_classification(self):
        desc = FileDescriptor(
            id="test-1",
            original_name="statement_october_2026.pdf",
            extension="pdf",
            size_bytes=10240,
            preview_text="Chase Bank Checking Statement Total Balance $4,500.00 Transaction history",
        )
        res = self.classifier.classify(desc)
        self.assertEqual(res.target_drawer, DrawerType.FINANCE)
        self.assertIn("statement", res.proposed_name)
        self.assertIn("chase", res.proposed_name)

    def test_code_and_log_classification(self):
        desc = FileDescriptor(
            id="test-2",
            original_name="crash_trace.log",
            extension="log",
            size_bytes=4096,
            preview_text="Traceback (most recent call last): File 'server.py', line 45, in <module> HTTPException: 500 Internal Server Error",
        )
        res = self.classifier.classify(desc)
        self.assertEqual(res.target_drawer, DrawerType.DEVELOPMENT)
        self.assertTrue(res.confidence > 0.6)

    def test_archive_classification(self):
        desc = FileDescriptor(
            id="test-3",
            original_name="backup_project_v1.tar.gz",
            extension="gz",
            size_bytes=50000000,
            preview_text="",
        )
        res = self.classifier.classify(desc)
        self.assertEqual(res.target_drawer, DrawerType.ARCHIVES)

    def test_screenshot_smart_renaming(self):
        desc = FileDescriptor(
            id="test-4",
            original_name="Screenshot 2026-10-24 at 11.23.41 PM.png",
            extension="png",
            size_bytes=520000,
            preview_text="Figma CSS flexbox grid alignment issue layout",
        )
        res = self.classifier.classify(desc)
        self.assertEqual(res.target_drawer, DrawerType.MEDIA)
        self.assertTrue(res.proposed_name.startswith("screenshot_"))
        self.assertTrue(res.proposed_name.endswith(".png"))
        self.assertNotIn("11.23.41", res.proposed_name)  # Cleaned up time spam

    def test_date_extraction(self):
        self.assertEqual(extract_date("invoice_2026-10-15.pdf"), "2026-10-15")
        self.assertEqual(extract_date("statement_october_2026.pdf"), "2026-10")
        self.assertEqual(extract_date("receipt_20261020.pdf"), "2026-10-20")

    def test_sanitize_slug(self):
        self.assertEqual(sanitize_slug("My Messy File (1)!.pdf"), "my_messy_file_1_pdf")


if __name__ == "__main__":
    unittest.main()
