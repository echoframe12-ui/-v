"""Tests for claude_adapter.py — official Anthropic Claude model adapter.

Covers:
  - create_claude_adapter returns None without ANTHROPIC_API_KEY
  - generate() returns structured output dictionary
  - generate() handles refusal as structured error
  - describe() includes model and keywords
  - router correctly routes prompt containing 'claude'
  - generate() handles RateLimitError gracefully
  - generate() handles APIStatusError gracefully
  - generate() handles APIConnectionError gracefully
  - create_claude_adapter creates instance when API key present
"""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from claude_adapter import ClaudeAdapter, create_claude_adapter
from models import ModelAdapter, ModelRouter


def make_response(text="Hello from Claude", stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        model="claude-opus-4-8",
    )


class ClaudeAdapterTests(unittest.TestCase):

    def test_factory_returns_none_without_api_key(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("ANTHROPIC_API_KEY", None)
            self.assertIsNone(create_claude_adapter())

    def test_generate_returns_text_output(self):
        client = MagicMock()
        client.messages.create.return_value = make_response()
        adapter = ClaudeAdapter(client=client)

        result = adapter.generate("Summarize the charter")

        self.assertEqual(result["output"], "Hello from Claude")
        self.assertEqual(result["provider"], "anthropic")
        call_kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "claude-opus-4-8")
        self.assertEqual(call_kwargs["thinking"], {"type": "adaptive"})

    def test_generate_reports_refusal_as_error(self):
        client = MagicMock()
        client.messages.create.return_value = make_response(stop_reason="refusal")
        adapter = ClaudeAdapter(client=client)

        result = adapter.generate("A declined request")

        self.assertEqual(result["error"], "refusal")
        self.assertNotIn("output", result)

    def test_describe_includes_model(self):
        client = MagicMock()
        adapter = ClaudeAdapter(client=client, keywords=["claude"])
        description = adapter.describe()
        self.assertEqual(description["model"], "claude-opus-4-8")
        self.assertEqual(description["keywords"], ["claude"])

    def test_router_routes_claude_prompts_to_adapter(self):
        client = MagicMock()
        client.messages.create.return_value = make_response()
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        router.register(ClaudeAdapter(client=client, keywords=["claude"]))

        routed = router.route("Ask claude about the charter")
        self.assertEqual(routed["adapter"], "claude")

        fallback = router.route("hello")
        self.assertEqual(fallback["adapter"], "local")

    def test_rate_limit_error_handled_gracefully(self):
        import anthropic
        client = MagicMock()
        client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body={}
        )
        adapter = ClaudeAdapter(client=client)
        result = adapter.generate("Heavy query")
        self.assertEqual(result["error"], "rate_limited")

    def test_api_status_error_handled_gracefully(self):
        import anthropic
        client = MagicMock()
        error_resp = MagicMock(status_code=500)
        client.messages.create.side_effect = anthropic.APIStatusError(
            message="Internal server error",
            response=error_resp,
            body={}
        )
        adapter = ClaudeAdapter(client=client)
        result = adapter.generate("Error query")
        self.assertEqual(result["error"], "api_error_500")

    def test_api_connection_error_handled_gracefully(self):
        import anthropic
        client = MagicMock()
        client.messages.create.side_effect = anthropic.APIConnectionError(
            request=MagicMock()
        )
        adapter = ClaudeAdapter(client=client)
        result = adapter.generate("Offline query")
        self.assertEqual(result["error"], "connection_error")

    def test_factory_with_api_key(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-fake-key"}, clear=False):
            client_mock = MagicMock()
            with patch("anthropic.Anthropic", return_value=client_mock):
                adapter = create_claude_adapter()
                self.assertIsNotNone(adapter)
                self.assertEqual(adapter.provider, "anthropic")


if __name__ == "__main__":
    unittest.main()

