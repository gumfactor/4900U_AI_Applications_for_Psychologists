from __future__ import annotations

import json
from urllib import error, request


class GeminiClient:
    API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def generate(self, prompt: str, model: str) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured.")

        url = f"{self.API_ROOT}/{model}:generateContent?key={self.api_key}"
        payload = json.dumps(
            {"contents": [{"parts": [{"text": prompt}]}]}
        ).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"Gemini request failed: {exc.code} {exc.reason}") from exc

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini response contained no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
