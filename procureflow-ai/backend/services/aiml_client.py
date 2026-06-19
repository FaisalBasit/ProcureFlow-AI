"""
AI/ML API client for OpenAI-compatible model inference.
Defaults to AI/ML API when configured, with OpenRouter as a local fallback.
Powers risk analysis, policy checks, and approval summaries.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "").strip().lower()
AIMLAPI_KEY = os.getenv("AIMLAPI_KEY") or os.getenv("AI_ML_API_KEY")
AIMLAPI_BASE_URL = os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1")
AIMLAPI_MODEL = os.getenv("AIMLAPI_MODEL", "google/gemma-3-4b-it")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


class AIMLClientError(Exception):
    pass


class AIMLClient:
    """Client for AI/ML API-compatible chat completions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider, self.provider_label, self.api_key, self.base_url, self.model = (
            self._resolve_provider(api_key=api_key, model=model)
        )
        if not self.api_key:
            raise AIMLClientError(
                "No model provider key is set. Add AIMLAPI_KEY for AI/ML API "
                "or OPENROUTER_API_KEY for the fallback provider."
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == "openrouter":
            self.headers["HTTP-Referer"] = "https://github.com/FaisalBasit/ProcureFlow-AI"

    def _resolve_provider(
        self,
        api_key: Optional[str],
        model: Optional[str],
    ) -> tuple[str, str, Optional[str], str, str]:
        requested = AI_PROVIDER.replace("-", "_").replace("/", "_")
        use_aimlapi = requested in ("aimlapi", "ai_ml_api", "aiml", "ai_ml")
        use_openrouter = requested == "openrouter"

        if (use_aimlapi and (api_key or AIMLAPI_KEY)) or (
            not use_openrouter and (api_key or AIMLAPI_KEY)
        ):
            return (
                "aimlapi",
                "AI/ML API",
                api_key or AIMLAPI_KEY,
                AIMLAPI_BASE_URL.rstrip("/"),
                model or AIMLAPI_MODEL,
            )

        return (
            "openrouter",
            "OpenRouter fallback",
            api_key or OPENROUTER_API_KEY,
            OPENROUTER_BASE_URL.rstrip("/"),
            model or OPENROUTER_MODEL,
        )

    def provider_metadata(self) -> Dict[str, str]:
        """Return non-secret provider metadata for audit logs and demo evidence."""
        return {
            "provider": self.provider_label,
            "provider_key": self.provider,
            "base_url": self.base_url,
            "model": self.model,
        }

    def _openrouter_fallback_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/FaisalBasit/ProcureFlow-AI",
        }

    async def _post_chat_completion(
        self,
        base_url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        provider_label: str,
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
        except httpx.ConnectError as e:
            raise AIMLClientError(f"Connection failed to {provider_label}: {e}")
        except httpx.TimeoutException as e:
            raise AIMLClientError(f"Timeout connecting to {provider_label}: {e}")
        except Exception as e:
            raise AIMLClientError(f"Unexpected error calling {provider_label}: {e}")

        if resp.status_code != 200:
            raise AIMLClientError(f"{provider_label} error: {resp.status_code} - {resp.text}")
        return resp.json()

    def _parse_json_object(self, content: str) -> Dict[str, Any]:
        """Parse a JSON object from model output, including fenced markdown JSON."""
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

        raise AIMLClientError("Model response did not contain a JSON object")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Send a chat completion request to the configured model provider."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            return await self._post_chat_completion(
                self.base_url,
                self.headers,
                payload,
                self.provider_label,
            )
        except AIMLClientError as primary_error:
            if self.provider != "aimlapi" or not OPENROUTER_API_KEY:
                raise

            fallback_payload = {**payload, "model": OPENROUTER_MODEL}
            try:
                result = await self._post_chat_completion(
                    OPENROUTER_BASE_URL.rstrip("/"),
                    self._openrouter_fallback_headers(),
                    fallback_payload,
                    "OpenRouter fallback after AI/ML API failure",
                )
            except AIMLClientError as fallback_error:
                raise AIMLClientError(
                    f"{primary_error}; OpenRouter fallback also failed: {fallback_error}"
                )

            self.provider = "openrouter"
            self.provider_label = "OpenRouter fallback after AI/ML API failure"
            self.base_url = OPENROUTER_BASE_URL.rstrip("/")
            self.model = OPENROUTER_MODEL
            self.headers = self._openrouter_fallback_headers()
            return result

    async def analyze_vendor_risk(self, vendor_name: str, amount: float) -> Dict[str, Any]:
        """Analyze vendor risk using AI reasoning."""
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a procurement risk analyst. Analyze the vendor and purchase amount "
                    "and return a JSON object with: risk_score (1-10), risk_level (low/medium/high/critical), "
                    "concerns (list of strings), and recommendation (string). "
                    "Consider factors like: amount size relative to typical procurement, "
                    "vendor name reputation signals, category risks."
                ),
            },
            {
                "role": "user",
                "content": f"Vendor: {vendor_name}\nAmount: ${amount:,.2f}\nAnalyze the risk.",
            },
        ]
        result = await self.chat_completion(prompt, temperature=0.3)
        content = result["choices"][0]["message"]["content"]
        try:
            parsed = self._parse_json_object(content)
            parsed["model_provider"] = self.provider_metadata()
            return parsed
        except AIMLClientError:
            return {
                "risk_score": 5,
                "risk_level": "medium",
                "concerns": ["Unable to parse AI response as structured JSON"],
                "recommendation": content,
                "model_provider": self.provider_metadata(),
            }

    async def generate_summary(self, context: Dict[str, Any]) -> str:
        """Generate a human-readable summary from agent context."""
        prompt = [
            {
                "role": "system",
                "content": "You are a procurement decision summarizer. Create a concise, clear summary "
                           "of the following procurement analysis for a human approver. Include key facts, "
                           "risk assessment, policy compliance status, and a clear recommendation.",
            },
            {
                "role": "user",
                "content": json.dumps(context, indent=2),
            },
        ]
        result = await self.chat_completion(prompt, temperature=0.4, max_tokens=1024)
        return result["choices"][0]["message"]["content"]

    async def check_policy_compliance(
        self, vendor_name: str, amount: float, category: str, justification: str
    ) -> Dict[str, Any]:
        """Check a purchase request against company procurement policies."""
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a procurement policy compliance officer. Check the purchase request "
                    "against these company policies and return JSON:\n"
                    "{\n"
                    '  "compliant": true/false,\n'
                    '  "policy_checks": [{"rule": "...", "passed": true/false, "reason": "..."}],\n'
                    '  "verdict": "approved/flagged/rejected",\n'
                    '  "notes": "..."\n'
                    "}\n\n"
                    "Policies:\n"
                    "1. Purchases over $10,000 require VP approval\n"
                    "2. Software subscriptions over $500/month require IT review\n"
                    "3. Consulting services over $25,000 require competitive bidding\n"
                    "4. New vendors (not previously approved) require enhanced due diligence\n"
                    "5. Capital expenses over $50,000 require board approval\n"
                    "6. All purchases must have a clear business justification\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Request Details:\n"
                    f"Vendor: {vendor_name}\n"
                    f"Amount: ${amount:,.2f}\n"
                    f"Category: {category}\n"
                    f"Justification: {justification}\n"
                    f"Please check compliance."
                ),
            },
        ]
        result = await self.chat_completion(prompt, temperature=0.2, max_tokens=1024)
        content = result["choices"][0]["message"]["content"]
        try:
            parsed = self._parse_json_object(content)
            parsed["model_provider"] = self.provider_metadata()
            return parsed
        except AIMLClientError:
            return {
                "compliant": False,
                "policy_checks": [],
                "verdict": "flagged",
                "notes": "Policy check could not be parsed. Manual review required.",
                "model_provider": self.provider_metadata(),
            }
