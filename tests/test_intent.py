"""Tests for Lucky.Engine Chunk 1 intent refactor.

These target the intended API:
- engine._env(primary, *fallbacks)
- engine.extract_intent(query)
- engine.classify_intent_llm(query)
"""

import json
import os
import urllib.error
import unittest
from unittest.mock import patch


import engine


_ENV_KEYS = (
    "LUCKY_LLM_API_KEY",
    "HLCO_LLM_API_KEY",
    "LUCKY_LLM_API_URL",
    "HLCO_LLM_API_URL",
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestIntent(unittest.TestCase):
    def setUp(self):
        self._env_backup = dict(os.environ)
        for key in _ENV_KEYS:
            os.environ.pop(key, None)
        self._reset_caches()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        self._reset_caches()

    @staticmethod
    def _reset_caches():
        for name in list(vars(engine)):
            obj = getattr(engine, name, None)
            if callable(obj) and hasattr(obj, "cache_clear"):
                try:
                    obj.cache_clear()
                except Exception:
                    pass
            if isinstance(obj, dict) and (
                "env" in name.lower() or "cache" in name.lower()
            ):
                try:
                    obj.clear()
                except Exception:
                    pass

    def test_classify_llm_without_key_makes_no_request_and_returns_keyword_intent(self):
        with patch(
            "engine.urllib.request.urlopen",
            side_effect=RuntimeError("urlopen must not be called"),
        ) as mock_urlopen:
            result = engine.classify_intent_llm("my finances")
        self.assertEqual(result, "financial")
        mock_urlopen.assert_not_called()

    def test_classify_llm_with_key_sends_auth_header_and_returns_intent(self):
        os.environ["LUCKY_LLM_API_KEY"] = "secret"
        self._reset_caches()

        captured = {}

        def fake_request(url, data=None, headers=None, method=None):
            captured["headers"] = dict(headers or {})
            captured["url"] = url
            captured["method"] = method
            return object()

        response = _FakeResponse(
            b'{"choices": [{"message": {"content": "financial"}}]}'
        )
        with patch("engine.urllib.request.Request", side_effect=fake_request), patch(
            "engine.urllib.request.urlopen", return_value=response
        ) as mock_urlopen:
            result = engine.classify_intent_llm("irrelevant query")

        self.assertEqual(result, "financial")
        mock_urlopen.assert_called_once()
        self.assertEqual(captured.get("headers", {}).get("Authorization"), "Bearer secret")

    def test_classify_llm_request_error_falls_back_to_keyword_intent(self):
        os.environ["LUCKY_LLM_API_KEY"] = "secret"
        self._reset_caches()

        with patch(
            "engine.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            result = engine.classify_intent_llm("move plan queries")

        self.assertEqual(result, "relocation")

    def test_extract_intent_fallback_not_always_general(self):
        result = engine.extract_intent("tailscale network")
        self.assertEqual(result, "network")


if __name__ == "__main__":
    unittest.main()
