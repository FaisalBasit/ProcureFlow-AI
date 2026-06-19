"""
@ApprovalAgent — ProcureFlow AI
Summarizes findings from all agents, presents to human for approval,
and generates the final SHA-256 audit packet on decision.
"""

import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.band_client import BandClient, BandClientError
from backend.services.aiml_client import AIMLClient, AIMLClientError
from backend.services.audit import generate_audit_packet
from backend.db.supabase_client import SupabaseDBClient

load_dotenv()


class ApprovalAgent:
    """
    Final approval agent. Gathers all context, generates human-readable summary,
    waits for human decision, and seals the audit packet.
    """

    def __init__(self):
        self.band = BandClient()
        self.ai = AIMLClient()
        self.db = SupabaseDBClient()

    async def prepare_for_approval(self, request_id: str) -> Dict[str, Any]:
        """
        Gather all agent outputs from DB + Band context, generate summary,
        and present for human approval.
        """
        # Get request details
        request = await self.db.get_request(request_id)
        if not request:
            return {"status": "error", "message": f"Request {request_id} not found"}

        # Get all agent logs
        logs = await self.db.get_agent_logs(request_id)

        # Extract agent outputs
        intake_output = {}
        risk_output = {}
        policy_output = {}
        open_source_review = {}

        for log in logs:
            if log["agent_name"] == "IntakeAgent":
                intake_output = log["output"]
            elif log["agent_name"] == "RiskAgent":
                risk_output = log["output"]
            elif log["agent_name"] == "PolicyAgent":
                policy_output = log["output"]
            elif log["agent_name"] == "FeatherlessReviewAgent":
                open_source_review = log["output"]

        # Build context for AI summary
        context = {
            "request_id": request_id,
            "vendor_name": request["vendor_name"],
            "amount": request["amount"],
            "category": request["category"],
            "justification": request["justification"],
            "risk_assessment": risk_output,
            "policy_compliance": policy_output,
            "open_source_review": open_source_review,
        }

        # Generate AI summary
        try:
            summary = await self.ai.generate_summary(context)
        except AIMLClientError as e:
            summary = f"Summary generation unavailable: {str(e)}"

        # Log approval agent action
        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="ApprovalAgent",
            action="approval_summary_generated",
            output={
                "summary": summary,
                "context": context,
                "model_provider": self.ai.provider_metadata(),
            },
        )

        # Post approval summary to Band room
        band_message = {
            "type": "approval_summary",
            "request_id": request_id,
            "vendor_name": request["vendor_name"],
            "amount": request["amount"],
            "summary": summary,
            "model_provider": self.ai.provider_metadata(),
            "status": "awaiting_human_approval",
        }

        await self.db.update_request_status(request_id, "awaiting_approval")
        try:
            band_result = await self.band.send_message(band_message, "ApprovalAgent")
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "ApprovalAgent",
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
        except BandClientError as e:
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "ApprovalAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": "ready_for_approval",
            "request_id": request_id,
            "summary": summary,
            "context": context,
        }

    async def process_human_decision(
        self,
        request_id: str,
        approved: bool,
        signed_by: str,
    ) -> Dict[str, Any]:
        """
        Process the human approver's decision. Generates audit packet with SHA-256 seal.
        """
        # Get request and all agent outputs
        request = await self.db.get_request(request_id)
        if not request:
            return {"status": "error", "message": f"Request {request_id} not found"}

        logs = await self.db.get_agent_logs(request_id)

        intake_output = {}
        risk_output = {}
        policy_output = {}
        open_source_review = {}
        summary_output = {}

        for log in logs:
            if log["agent_name"] == "IntakeAgent":
                intake_output = log["output"]
            elif log["agent_name"] == "RiskAgent":
                risk_output = log["output"]
            elif log["agent_name"] == "PolicyAgent":
                policy_output = log["output"]
            elif log["agent_name"] == "FeatherlessReviewAgent":
                open_source_review = log["output"]
            elif log["agent_name"] == "ApprovalAgent":
                summary_output = log["output"]

        final_status = "approved" if approved else "rejected"

        # Generate the SHA-256 audit packet
        audit_packet = generate_audit_packet(
            request_id=request_id,
            vendor_name=request["vendor_name"],
            amount=float(request["amount"]),
            category=request["category"],
            justification=request["justification"],
            risk_report=risk_output,
            policy_verdict=policy_output,
            open_source_review=open_source_review,
            approval_summary=summary_output.get("summary", ""),
            human_decision=final_status,
            signed_by=signed_by,
        )

        # Record decision in database
        await self.db.record_decision(
            request_id=request_id,
            human_approved=approved,
            audit_hash=audit_packet["audit_hash"],
            signed_by=signed_by,
        )

        # Log final action
        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="ApprovalAgent",
            action="decision_finalized",
            output=audit_packet,
        )

        # Post final decision to Band room
        band_message = {
            "type": "final_decision",
            "request_id": request_id,
            "vendor_name": request["vendor_name"],
            "approved": approved,
            "audit_hash": audit_packet["audit_hash"],
            "status": final_status,
        }

        await self.db.update_request_status(request_id, final_status)
        try:
            band_result = await self.band.send_message(band_message, "ApprovalAgent")
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "ApprovalAgent",
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
        except BandClientError as e:
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "ApprovalAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": final_status,
            "request_id": request_id,
            "audit_packet": audit_packet,
        }

    async def process_band_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming Band room message.
        If it's a policy verdict (approved/flagged), prepare for approval.
        If it's a human decision, finalize.
        """
        content_type = message.get("content", {}).get("type", "")
        content = message.get("content", {})

        if content_type == "policy_verdict" and content.get("status") in (
            "approved", "flagged_for_review", "pending_approval"
        ):
            if content.get("human_visible", True):
                request_id = content["request_id"]
                return await self.prepare_for_approval(request_id)

        elif content_type == "human_decision":
            request_id = content["request_id"]
            approved = content.get("approved", False)
            signed_by = content.get("signed_by", "unknown")
            return await self.process_human_decision(request_id, approved, signed_by)

        return None
