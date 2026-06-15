"""
AI/ML API client — uses OpenRouter for model inference.
Powers @RiskAgent with vendor risk analysis, summarization, and reasoning.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class AIMLClientError(Exception):
    pass


class AIMLClient:
    """Client for AI model inference via OpenRouter."""

    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key or OPENROUTER_API_KEY
        if not self.api_key:
            raise AIMLClientError("OPENROUTER_API_KEY is not set")
        self.base_url = OPENROUTER_BASE_URL
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/FaisalBasit/ProcureFlow-AI",
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Send a chat completion request to OpenRouter."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
        if resp.status_code != 200:
            raise AIMLClientError(f"OpenRouter API error: {resp.status_code} - {resp.text}")
        return resp.json()

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
        # Try to parse as JSON, fallback to structured text
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "risk_score": 5,
                "risk_level": "medium",
                "concerns": ["Unable to parse AI response as structured JSON"],
                "recommendation": content,
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
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "compliant": False,
                "policy_checks": [],
                "verdict": "flagged",
                "notes": "Policy check could not be parsed. Manual review required.",
            }