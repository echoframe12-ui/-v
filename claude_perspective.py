from __future__ import annotations

import os
from typing import Any

from context_assembly import ContextAssembly
from perspectives import Perspective, PerspectiveAdapter, make_perspective


class ClaudePerspectiveAdapter:
    """A PerspectiveAdapter for Anthropic's Claude models.

    Integrates with the `anthropic` package to generate a Perspective
    from an assembled ContextAssembly. Gracefully handles rate limits and API errors
    by returning an error response string rather than raising exceptions.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20240620",
        client: Any | None = None,
    ) -> None:
        self.provider = "anthropic"
        self.model = model
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client = client

    def generate(self, context: ContextAssembly) -> Perspective:
        import anthropic

        prompt = context.content
        perspective_id_base = f"{self.provider}-{self.model}-{context.content_hash[:8]}"

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.RateLimitError:
            return self._error_perspective(context, perspective_id_base, "error: rate_limited")
        except anthropic.APIStatusError as error:
            return self._error_perspective(context, perspective_id_base, f"error: api_error_{error.status_code}")
        except anthropic.APIConnectionError:
            return self._error_perspective(context, perspective_id_base, "error: connection_error")

        if response.stop_reason == "refusal":
            return self._error_perspective(context, perspective_id_base, "error: refusal")

        output = "".join(
            block.text for block in response.content if block.type == "text"
        )

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
