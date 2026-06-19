"""
@RiskAgent — ProcureFlow AI
Scores vendor risk using AI/ML API (OpenRouter).
Fetches request from Band room, runs risk analysis, posts result back.
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


class RiskAgent:
    """Analyzes vendor risk for purchase requests."""

    def __init__(self):
        self.band = BandClient()
        self.ai = AIMLClient()
        self.db = SupabaseDBClient()

    async def analyze_request(self, request_id: str) -> Dict[str, Any]:
        """
        Analyze the risk of a purchase request by reading from Band room context.
        """
        # Get request details from database
        request = await self.db.get_request(request_id)
        if not request:
            return {"status": "error", "message": f"Request {request_id} not found"}

        vendor_name = request["vendor_name"]
        amount = float(request["amount"])
        category = request["category"]
        justification = request["justification"]

        # Run AI risk analysis
        try:
            risk_report = await self.ai.analyze_vendor_risk(vendor_name, amount)
        except AIMLClientError as e:
            risk_report = {
                "risk_score": 5,
                "risk_level": "medium",
                "concerns": [f"AI analysis unavailable: {str(e)}"],
                "recommendation": "Manual review required due to AI service error.",
            }

        # Log to database
        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="RiskAgent",
            action="risk_analysis_complete",
            output=risk_report,
        )

        # Post risk report to Band room
        band_message = {
            "type": "risk_report",
            "request_id": request_id,
            "vendor_name": vendor_name,
            "risk_score": risk_report.get("risk_score", 5),
            "risk_level": risk_report.get("risk_level", "medium"),
            "concerns": risk_report.get("concerns", []),
            "recommendation": risk_report.get("recommendation", ""),
            "status": "pending_policy_check",
        }

        await self.db.update_request_status(request_id, "policy_check")
        try:
            band_result = await self.band.send_message(band_message, "RiskAgent")
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "RiskAgent",
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
            handoff_result = await self.band.send_handoff_message(
                source_agent_name="RiskAgent",
                target_agent_name="PolicyAgent",
                handoff=(
                    f"Risk report for request {request_id} is complete. "
                    f"Risk level: {risk_report.get('risk_level', 'medium')}; "
                    f"score: {risk_report.get('risk_score', 5)}/10. "
                    "Please run procurement policy compliance."
                ),
            )
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_handoff_posted",
                output={
                    "source_agent": "RiskAgent",
                    "target_agent": "PolicyAgent",
                    "band_result": handoff_result,
                },
            )
        except BandClientError as e:
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "RiskAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": "analyzed",
            "request_id": request_id,
            "risk_report": risk_report,
        }

    async def process_band_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming Band room message.
        If it's a purchase request, run risk analysis.
        """
        content_type = message.get("content", {}).get("type", "")
        if content_type == "purchase_request":
            request_id = message["content"]["request_id"]
            return await self.analyze_request(request_id)
        return None
