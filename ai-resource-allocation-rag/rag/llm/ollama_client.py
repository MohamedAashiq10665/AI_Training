from __future__ import annotations

import httpx

from backend.utils.config import settings


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    def generate(self, prompt: str, timeout_seconds: float = 60.0) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get("response", "No response returned by model.")
