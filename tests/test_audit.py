"""Tests for Lucky.Engine Chunk 6 audit fixes."""

import os
import tempfile
import unittest
from pathlib import Path

import engine


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.audit = self.tmp / "audit.md"
        self.orig = engine.AUDIT_LOG
        engine.AUDIT_LOG = self.audit
        # restore default graph/config not needed
    def tearDown(self):
        engine.AUDIT_LOG = self.orig

    def test_append_preserves_prior(self):
        engine.write_audit("q1", "intent", [], [], 1)
        engine.write_audit("q2", "intent", [], [], 2)
        text = self.audit.read_text(encoding="utf-8")
        self.assertIn("q1", text)
        self.assertIn("q2", text)

    def test_utf8_roundtrip(self):
        engine.write_audit("café", "intent", [], [], 1)
        text = self.audit.read_text(encoding="utf-8")
        self.assertIn("café", text)


if __name__ == "__main__":
    unittest.main()
