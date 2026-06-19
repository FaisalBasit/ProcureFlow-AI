"""
Featherless AI client for open-source model inference.
Runs an independent second-opinion review before human approval.
"""

import json
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
FEATHERLESS_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
FEATHERLESS_MODEL = os.getenv(
    "FEATHERLESS_MODEL",
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
)


class FeatherlessClientError(Exception):
    pass


class FeatherlessClient:
    """OpenAI-compatible client pointed at Featherless AI."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or FEATHERLESS_API_KEY
        self.base_url = FEATHERLESS_BASE_URL.rstrip("/")
        self.model = model or FEATHERLESS_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def provider_metadata(self) -> Dict[str, str]:
        return {
            "provider": "Featherless AI",
            "provider_key": "featherless",
            "base_url": self.base_url,
            "model": self.model,
        }

    def _parse_json_object(self, content: str) -> Dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(cleaned[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise FeatherlessClientError("Featherless response did not contain a JSON object")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Dict[str, Any]:
        if not self.configured:
            raise FeatherlessClientError("FEATHERLESS_API_KEY is not set")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )
        except httpx.ConnectError as e:
            raise FeatherlessClientError(f"Connection failed to Featherless AI: {e}")
        except httpx.TimeoutException as e:
            raise FeatherlessClientError(f"Timeout connecting to Featherless AI: {e}")
        except Exception as e:
            raise FeatherlessClientError(f"Unexpected error calling Featherless AI: {e}")

        if resp.status_code != 200:
            raise FeatherlessClientError(
                f"Featherless AI error: {resp.status_code} - {resp.text}"
            )
        return resp.json()

    async def review_procurement_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ask an open-source model to independently review the decision packet."""
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an independent procurement governance reviewer running on "
                    "Featherless AI open-source model inference. Review the request, "
                    "risk report, and policy verdict. Return strict JSON only with: "
                    "review_verdict (concur/escalate/reject), confidence (0-1), "
                    "concerns (array of strings), recommendation (string), "
                    "and reviewer_notes (string)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(context, indent=2, default=str),
            },
        ]

        result = await self.chat_completion(prompt)
        content = result["choices"][0]["message"]["content"]
        try:
            parsed = self._parse_json_object(content)
        except FeatherlessClientError:
            parsed = {
                "review_verdict": "escalate",
                "confidence": 0.4,
                "concerns": ["Unable to parse Featherless response as structured JSON"],
                "recommendation": content,
                "reviewer_notes": "Raw model output retained for human review.",
            }

        parsed["model_provider"] = self.provider_metadata()
        parsed["provider_status"] = "available"
        return parsed
