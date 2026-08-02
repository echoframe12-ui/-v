import unittest
from unittest.mock import MagicMock

from claude_perspective import ClaudePerspectiveAdapter
from context_assembly import ContextAssembler, ContextSource

class ClaudePerspectiveTests(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.adapter = ClaudePerspectiveAdapter(client=self.mock_client)
        self.context = ContextAssembler().assemble([ContextSource(ref="test", content="prompt content")])

    def test_generate_success(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.id = "msg-123"
        mock_response.model = "claude-3-5-sonnet-20240620"
        mock_response.stop_reason = "end_turn"
        
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello!"
        mock_response.content = [mock_block]
        
        self.mock_client.messages.create.return_value = mock_response

        # Execute
        perspective = self.adapter.generate(self.context)
        
        # Verify
        self.assertEqual(perspective.provider, "anthropic")
        self.assertEqual(perspective.response, "Hello!")
        self.assertEqual(perspective.model, "claude-3-5-sonnet-20240620")
        self.assertIn("msg-123", perspective.id)
        
        self.mock_client.messages.create.assert_called_once()
        call_kwargs = self.mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs["messages"][0]["content"], "[test]\nprompt content")

    def test_generate_rate_limit(self):
        import anthropic
        
        # We must mock RateLimitError properly. In newer SDKs, it requires args.
        # But for test purposes, simulating it by setting side_effect.
        class MockRateLimitError(anthropic.RateLimitError):
            def __init__(self):
                pass
                
        self.mock_client.messages.create.side_effect = MockRateLimitError()
        
        perspective = self.adapter.generate(self.context)
        
        self.assertEqual(perspective.response, "error: rate_limited")
        self.assertTrue(perspective.id.endswith("-err"))

if __name__ == "__main__":
    unittest.main()
