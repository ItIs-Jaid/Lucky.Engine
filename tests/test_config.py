"""Tests for Lucky.Engine Chunk 2 config parsing."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import engine


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._backup = dict(os.environ)
        self._tmp = Path(tempfile.mkdtemp())
        self._orig = engine.CONFIG_FILE

    def tearDown(self):
        engine.CONFIG_FILE = self._orig
        os.environ.clear()
        os.environ.update(self._backup)

    def _write(self, text):
        p = self._tmp / "cfg.yaml"
        p.write_text(text, encoding="utf-8")
        engine.CONFIG_FILE = p
        return p

    def test_nested_skill_weights_loaded(self):
        self._write("""max_tokens: 1000
confidence_threshold: 0.75
skill_weights:
  finances: 1.0
  memory-graph: 0.8
""")
        cfg = engine.load_config()
        self.assertEqual(cfg["skill_weights"], {"finances": 1.0, "memory-graph": 0.8})
        self.assertEqual(cfg["max_tokens"], 1000)
        self.assertEqual(cfg["confidence_threshold"], 0.75)

    def test_cache_enabled_and_fallback_budget(self):
        self._write("""cache_enabled: true
fallback_budget: 2000
""")
        cfg = engine.load_config()
        self.assertTrue(cfg["cache_enabled"])
        self.assertEqual(cfg["fallback_budget"], 2000)

    def test_missing_file_returns_full_defaults(self):
        engine.CONFIG_FILE = self._tmp / "nope.yaml"
        cfg = engine.load_config()
        for key in ("max_tokens", "confidence_threshold", "audit_max_lines", "default_budget", "fallback_budget", "cache_enabled", "skill_weights", "intent_keywords", "intent_priorities"):
            self.assertIn(key, cfg)
        self.assertFalse(cfg["cache_enabled"])
        self.assertEqual(cfg["skill_weights"], {})


if __name__ == "__main__":
    unittest.main()
