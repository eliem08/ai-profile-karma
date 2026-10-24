import json
import os
import tempfile
import unittest
from datetime import date

from ai_profile_karma import exposure_score, luhn_ok, request_letter, scan_path, scan_text

CHAT = ("Hi, I live in Austin at 1200 Oak Street. My email is jane.doe@example.com and phone (512) 555-0199. "
        "I was diagnosed with ADHD last year and my salary is 95k. My card 4111 1111 1111 1111 got declined.")


class Tests(unittest.TestCase):
    def test_luhn(self):
        self.assertTrue(luhn_ok("4111 1111 1111 1111"))
        self.assertFalse(luhn_ok("4111 1111 1111 1112"))

    def test_scan_text(self):
        kinds = {(f.category, f.kind) for f in scan_text(CHAT)}
        for expected in [("pii", "email"), ("pii", "phone"), ("pii", "address"), ("pii", "payment_card")]:
            self.assertIn(expected, kinds)
        cats = {c for c, _ in kinds}
        self.assertTrue({"health", "finances", "location"} <= cats)

    def test_masking(self):
        email = next(f for f in scan_text(CHAT) if f.kind == "email")
        self.assertNotIn("jane.doe@example.com", email.snippet)

    def test_scan_json_export_and_score(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "conversations.json"), "w") as fh:
                json.dump([{"title": "t", "mapping": {"a": {"message": {"content": {"parts": [CHAT]}}}}}], fh)
            rep = exposure_score(scan_path(d))
            self.assertGreaterEqual(rep["score"], 60)
            self.assertEqual(rep["level"], "high")
        self.assertEqual(exposure_score([])["score"], 0)

    def test_letter(self):
        txt = request_letter("ExampleAI", "gdpr", "delete", "Jane", "j@x.com", ["health"], today=date(2026, 10, 24))
        self.assertIn("Article 17", txt)
        self.assertIn("health", txt)
        self.assertIn("45 days", request_letter("X", "ccpa", "access", "J", "j@x", today=date(2026, 1, 1)))


if __name__ == "__main__":
    unittest.main()
