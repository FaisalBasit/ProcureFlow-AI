"""
@FeatherlessReviewAgent - ProcureFlow AI
Runs an independent open-source model review through Featherless AI before
the human approval packet is generated.
"""

import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db.supabase_client import SupabaseDBClient
from backend.services.band_client import BandClient, BandClientError
from backend.services.featherless_client import FeatherlessClient, FeatherlessClientError

load_dotenv()


class FeatherlessReviewAgent:
    """
    Independent second-opinion agent backed by Featherless open-source model inference.
    It strengthens the human approval step with a separate model provider.
    """

    def __init__(self):
        self.band = BandClient()
        self.featherless = FeatherlessClient()
        self.db = SupabaseDBClient()

    def _band_sender_agent(self) -> str:
        """Use a fifth Band agent when configured; otherwise attach review to PolicyAgent."""
        has_review_agent_key = (
            os.getenv("BAND_FEATHERLESS_REVIEW_AGENT_API_KEY")
            or os.getenv("BAND_FEATHERLESS_REVIEW_API_KEY")
            or os.getenv("BAND_FEATHERLESS_API_KEY")
        )
        return "FeatherlessReviewAgent" if has_review_agent_key else "PolicyAgent"

    async def review_request(self, request_id: str) -> Dict[str, Any]:
        request = await self.db.get_request(request_id)
        if not request:
            return {"status": "error", "message": f"Request {request_id} not found"}

        logs = await self.db.get_agent_logs(request_id)
        risk_output: Dict[str, Any] = {}
        policy_output: Dict[str, Any] = {}

        for log in logs:
            if log["agent_name"] == "RiskAgent":
                risk_output = log["output"]
            elif log["agent_name"] == "PolicyAgent":
                policy_output = log["output"]

        review_context = {
            "request_id": request_id,
            "vendor_name": request["vendor_name"],
            "amount": request["amount"],
            "category": request["category"],
            "justification": request["justification"],
            "risk_assessment": risk_output,
            "policy_compliance": policy_output,
        }

        try:
            review = await self.featherless.review_procurement_decision(review_context)
            action = "open_source_review_complete"
            workflow_status = "reviewed"
            event_status = "open_source_review_complete"
        except FeatherlessClientError as e:
            review = {
                "review_verdict": "not configured",
                "confidence": 0,
                "concerns": [f"Featherless AI review unavailable: {str(e)}"],
                "recommendation": (
                    "Optional Featherless AI review is not configured. The workflow "
                    "continues with AI risk analysis, policy review, and human approval."
                ),
                "reviewer_notes": "Set FEATHERLESS_API_KEY to enable live open-source model review.",
                "provider_status": "not configured",
                "model_provider": self.featherless.provider_metadata(),
            }
            action = "open_source_review_unavailable"
            workflow_status = "unavailable"
            event_status = "open_source_review_unavailable"

        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="FeatherlessReviewAgent",
            action=action,
            output={
                **review,
                "review_context": review_context,
            },
        )

        band_message = {
            "type": "featherless_review",
            "request_id": request_id,
            "vendor_name": request["vendor_name"],
            "provider": "Featherless AI",
            "provider_status": review.get("provider_status", "available"),
            "review_verdict": review.get("review_verdict"),
            "confidence": review.get("confidence"),
            "recommendation": review.get("recommendation", ""),
            "status": event_status,
        }

        await self.db.update_request_status(request_id, "pending_approval")
        band_sender_agent = self._band_sender_agent()
        try:
            band_result = await self.band.send_message(band_message, band_sender_agent)
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "FeatherlessReviewAgent",
                    "band_sender_agent": band_sender_agent,
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
            handoff_result = await self.band.send_handoff_message(
                source_agent_name=band_sender_agent,
                target_agent_name="ApprovalAgent",
                handoff=(
                    f"Open-source review for request {request_id} is complete. "
                    f"Verdict: {review.get('review_verdict')}; "
                    f"provider status: {review.get('provider_status', 'available')}. "
                    "Please prepare the human approval memo with this second opinion."
                ),
            )
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_handoff_posted",
                output={
                    "source_agent": "FeatherlessReviewAgent",
                    "band_sender_agent": band_sender_agent,
                    "target_agent": "ApprovalAgent",
                    "band_result": handoff_result,
                },
            )
        except BandClientError as e:
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "FeatherlessReviewAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": workflow_status,
            "request_id": request_id,
            "open_source_review": review,
        }

    async def process_band_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        content_type = message.get("content", {}).get("type", "")
        if content_type == "policy_verdict" and message.get("content", {}).get("human_visible", True):
            return await self.review_request(message["content"]["request_id"])
        return None
