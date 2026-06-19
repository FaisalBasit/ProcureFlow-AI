"""
@PolicyAgent — ProcureFlow AI
Checks purchase requests against company procurement policy rules.
Uses CrewAI-style role definition and task execution.
Can veto requests before they reach human approval.
"""

import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.band_client import BandClient, BandClientError
from backend.services.aiml_client import AIMLClient, AIMLClientError
from backend.db.supabase_client import SupabaseDBClient

load_dotenv()


class PolicyAgent:
    """
    Policy compliance agent.
    Checks requests against procurement policies and can veto non-compliant requests.
    """

    def __init__(self):
        self.band = BandClient()
        self.ai = AIMLClient()
        self.db = SupabaseDBClient()

    async def check_compliance(self, request_id: str) -> Dict[str, Any]:
        """
        Check a purchase request against company procurement policies.
        Reads risk report from Band room context and runs policy check.
        """
        # Get request details from database
        request = await self.db.get_request(request_id)
        if not request:
            return {"status": "error", "message": f"Request {request_id} not found"}

        vendor_name = request["vendor_name"]
        amount = float(request["amount"])
        category = request["category"]
        justification = request["justification"]

        # Get agent logs for context
        logs = await self.db.get_agent_logs(request_id)
        risk_report = {}
        for log in logs:
            if log["agent_name"] == "RiskAgent":
                risk_report = log["output"]

        # Run AI policy compliance check
        try:
            policy_result = await self.ai.check_policy_compliance(
                vendor_name, amount, category, justification
            )
        except AIMLClientError as e:
            policy_result = {
                "compliant": False,
                "policy_checks": [],
                "verdict": "flagged",
                "notes": f"Policy check failed due to AI error: {str(e)}",
                "model_provider": self.ai.provider_metadata(),
            }

        # Determine next status based on verdict
        verdict = policy_result.get("verdict", "flagged")
        if verdict == "rejected":
            next_status = "rejected_by_policy"
            human_visible = False
        elif verdict == "flagged":
            next_status = "flagged_for_review"
            human_visible = True
        else:
            next_status = "pending_approval"
            human_visible = True

        # Log to database
        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="PolicyAgent",
            action="policy_check_complete",
            output={
                "verdict": verdict,
                "policy_checks": policy_result.get("policy_checks", []),
                "notes": policy_result.get("notes", ""),
                "human_visible": human_visible,
                "model_provider": policy_result.get("model_provider", self.ai.provider_metadata()),
            },
        )

        # Post policy verdict to Band room
        band_message = {
            "type": "policy_verdict",
            "request_id": request_id,
            "vendor_name": vendor_name,
            "compliant": policy_result.get("compliant", False),
            "verdict": verdict,
            "policy_checks": policy_result.get("policy_checks", []),
            "notes": policy_result.get("notes", ""),
            "model_provider": policy_result.get("model_provider", self.ai.provider_metadata()),
            "status": next_status,
            "human_visible": human_visible,
        }

        await self.db.update_request_status(request_id, next_status)
        try:
            band_result = await self.band.send_message(band_message, "PolicyAgent")
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "PolicyAgent",
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
            has_featherless_band_agent = (
                os.getenv("BAND_FEATHERLESS_REVIEW_AGENT_API_KEY")
                or os.getenv("BAND_FEATHERLESS_REVIEW_API_KEY")
                or os.getenv("BAND_FEATHERLESS_API_KEY")
            )
            target_agent = "FeatherlessReviewAgent" if has_featherless_band_agent else "ApprovalAgent"
            next_step = (
                "Please run the independent Featherless open-source review before approval."
                if has_featherless_band_agent
                else "The backend will run the Featherless open-source review, then prepare the approval memo."
            )
            handoff_result = await self.band.send_handoff_message(
                source_agent_name="PolicyAgent",
                target_agent_name=target_agent,
                handoff=(
                    f"Policy verdict for request {request_id} is {verdict}. "
                    f"Human-visible: {human_visible}. "
                    f"{next_step}"
                ),
            )
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_handoff_posted",
                output={
                    "source_agent": "PolicyAgent",
                    "target_agent": target_agent,
                    "band_result": handoff_result,
                },
            )
        except BandClientError as e:
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "PolicyAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": "checked",
            "request_id": request_id,
            "verdict": verdict,
            "policy_checks": policy_result.get("policy_checks", []),
            "human_visible": human_visible,
        }

    async def process_band_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming Band room message.
        If it's a risk report, run policy check.
        """
        content_type = message.get("content", {}).get("type", "")
        if content_type == "risk_report":
            request_id = message["content"]["request_id"]
            return await self.check_compliance(request_id)
        return None
