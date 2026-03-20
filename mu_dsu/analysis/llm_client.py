"""LLM client — OpenRouter API via OpenAI SDK."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def _load_api_key() -> str:
    """Load API key from .env file or environment."""
    # Try .env in project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set in .env or environment")
    return key


class LLMClient:
    """Thin wrapper around OpenRouter API."""

    def __init__(
        self,
        model: str = "google/gemini-3-flash-preview",
        base_url: str = "https://openrouter.ai/api/v1",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key or _load_api_key(),
        )

    def ask(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the response text."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def ask_json(self, prompt: str, system: str = "") -> str:
        """Send a prompt requesting JSON output."""
        if system:
            system += "\n\nIMPORTANT: Respond ONLY with valid JSON, no markdown fences."
        else:
            system = "Respond ONLY with valid JSON, no markdown fences."

        return self.ask(prompt, system)
