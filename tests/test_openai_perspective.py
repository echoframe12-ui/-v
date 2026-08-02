import unittest
from unittest.mock import MagicMock

from openai_perspective import OpenAIPerspectiveAdapter
from context_assembly import ContextAssembler, ContextSource

class OpenAIPerspectiveTests(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.adapter = OpenAIPerspectiveAdapter(client=self.mock_client)
        self.context = ContextAssembler().assemble([ContextSource(ref="test", content="prompt content")])

    def test_generate_success(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4o-2024-05-13"
        
        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message.content = "Hello from OpenAI!"
        
        mock_response.choices = [mock_choice]
        
        self.mock_client.chat.completions.create.return_value = mock_response

        # Execute
        perspective = self.adapter.generate(self.context)
        
        # Verify
        self.assertEqual(perspective.provider, "openai")
        self.assertEqual(perspective.response, "Hello from OpenAI!")
        self.assertEqual(perspective.model, "gpt-4o-2024-05-13")
        self.assertIn("chatcmpl-123", perspective.id)
        
        self.mock_client.chat.completions.create.assert_called_once()
        call_kwargs = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs["messages"][0]["content"], "[test]\nprompt content")

    def test_generate_rate_limit(self):
        import openai
        
        class MockRateLimitError(openai.RateLimitError):
            def __init__(self):
                pass
                
        self.mock_client.chat.completions.create.side_effect = MockRateLimitError()
        
        perspective = self.adapter.generate(self.context)
        
        self.assertEqual(perspective.response, "error: rate_limited")
        self.assertTrue(perspective.id.endswith("-err"))

if __name__ == "__main__":
    unittest.main()
