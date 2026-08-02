from __future__ import annotations

import os
from typing import Any

from context_assembly import ContextAssembly
from perspectives import Perspective, PerspectiveAdapter, make_perspective


class OpenAIPerspectiveAdapter:
    """A PerspectiveAdapter for OpenAI's GPT models.

    Integrates with the `openai` package to generate a Perspective
    from an assembled ContextAssembly. Gracefully handles rate limits and API errors
    by returning an error response string rather than raising exceptions.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        client: Any | None = None,
    ) -> None:
        self.provider = "openai"
        self.model = model
        if client is None:
            import openai

            client = openai.OpenAI()
        self._client = client

    def generate(self, context: ContextAssembly) -> Perspective:
        import openai

        prompt = context.content
        perspective_id_base = f"{self.provider}-{self.model}-{context.content_hash[:8]}"

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
        except openai.RateLimitError:
            return self._error_perspective(context, perspective_id_base, "error: rate_limited")
        except openai.APIError as error:
            return self._error_perspective(context, perspective_id_base, f"error: api_error_{error.code or 'unknown'}")
        except openai.APIConnectionError:
            return self._error_perspective(context, perspective_id_base, "error: connection_error")

        choice = response.choices[0]
        if choice.finish_reason != "stop" and choice.finish_reason != "length":
            return self._error_perspective(context, perspective_id_base, f"error: {choice.finish_reason}")

        output = choice.message.content or ""

        return make_perspective(
            perspective_id=f"{perspective_id_base}-{response.id}",
            provider=self.provider,
            model=response.model,
            response=output,
            context=context,
        )

    def _error_perspective(
        self, context: ContextAssembly, perspective_id_base: str, error_msg: str
    ) -> Perspective:
        return make_perspective(
            perspective_id=f"{perspective_id_base}-err",
            provider=self.provider,
            model=self.model,
            response=error_msg,
            context=context,
        )
