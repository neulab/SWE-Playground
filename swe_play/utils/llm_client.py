"""LLM client utility for making calls to LLMs compatible with the OpenAI's API."""

import os
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion


class LLMClient:
    """Client for making calls to LLM models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "neulab/claude-sonnet-4-20250514",
        base_url: str | None = None,
    ):
        """Initialize the LLM client.

        Args:
            api_key: LLM API key. If None, will try to get from OPENAI_API_KEY env var.
            model: The model to use for completions.
            base_url: Base URL for the API endpoint. If None, will try to get from
                OPENAI_BASE_URL env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LLM API key is required. Set OPENAI_API_KEY environment variable or pass "
                "api_key parameter."
            )

        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if not self.base_url:
            raise ValueError(
                "LLM base URL is required. Set OPENAI_BASE_URL environment variable or pass "
                "base_url parameter."
            )

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Make a chat completion request.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            temperature: Controls randomness in the response (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional arguments to pass to the OpenAI API.

        Returns:
            The generated text response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            if not response.choices:
                raise Exception("No response choices received from OpenAI API")

            return response.choices[0].message.content or ""

        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")

    def simple_completion(
        self, prompt: str, temperature: float = 0.7, max_tokens: int | None = None, **kwargs: Any
    ) -> str:
        """Make a simple completion request with a single user message.

        Args:
            prompt: The prompt text to send to the model.
            temperature: Controls randomness in the response (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional arguments to pass to the OpenAI API.

        Returns:
            The generated text response.
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, temperature, max_tokens, **kwargs)

    def system_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Make a completion request with a system message and user message.

        Args:
            system_prompt: The system prompt to set the context.
            user_prompt: The user prompt to send to the model.
            temperature: Controls randomness in the response (0.0 to 2.0).
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional arguments to pass to the OpenAI API.

        Returns:
            The generated text response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat_completion(messages, temperature, max_tokens, **kwargs)


def create_llm_client(
    api_key: str | None = None,
    model: str = "neulab/claude-sonnet-4-20250514",
    base_url: str | None = None,
) -> LLMClient:
    """Create a new LLM client instance.

    Args:
        api_key: OpenAI API key. If None, will try to get from OPENAI_API_KEY env var.
        model: The model to use for completions.
        base_url: Base URL for the API endpoint. If None, will try to get from
            OPENAI_BASE_URL env var, then use default.

    Returns:
        A configured LLMClient instance.
    """
    return LLMClient(api_key=api_key, model=model, base_url=base_url)
