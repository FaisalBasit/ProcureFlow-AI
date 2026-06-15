"""
Band webhook receiver for ProcureFlow AI.
Receives real-time messages from Band rooms and routes them to the appropriate agent.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os
import hmac
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.risk_agent import RiskAgent
from agents.policy_agent import PolicyAgent
from agents.approval_agent import ApprovalAgent
from backend.db.supabase_client import SupabaseDBClient

router = APIRouter(prefix="/api/webhook", tags=["webhook"])

# Agent instances
risk_agent = RiskAgent()
policy_agent = PolicyAgent()
approval_agent = ApprovalAgent()
db_client = SupabaseDBClient()


class BandWebhookPayload(BaseModel):
    event: str
    room_id: str
    message: Optional[Dict[str, Any]] = None
    agent: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


@router.post("/band")
async def band_webhook(payload: BandWebhookPayload, request: Request):
    """
    Receive webhook events from Band.
    Routes messages to the appropriate agent based on content type.
    """
    # Verify webhook signature if secret is configured
    webhook_secret = os.getenv("BAND_WEBHOOK_SECRET")
    if webhook_secret:
        signature = request.headers.get("X-Band-Signature")
        if signature:
            body = await request.body()
            expected_sig = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Only process message events
    if payload.event != "message" or not payload.content:
        return {"status": "ignored", "reason": "Not a message event"}

    content = payload.content
    message_type = content.get("type", "")

    try:
        processed_by = None
        result = None

        if message_type == "purchase_request":
            # Route to RiskAgent
            result = await risk_agent.process_band_message(
                {"content": content, "agent": payload.agent}
            )
            processed_by = "RiskAgent"

        elif message_type == "risk_report":
            # Route to PolicyAgent
            result = await policy_agent.process_band_message(
                {"content": content, "agent": payload.agent}
            )
            processed_by = "PolicyAgent"

        elif message_type == "policy_verdict":
            # Route to ApprovalAgent
            result = await approval_agent.process_band_message(
                {"content": content, "agent": payload.agent}
            )
            processed_by = "ApprovalAgent"

        elif message_type == "human_decision":
            # Route to ApprovalAgent for finalization
            result = await approval_agent.process_band_message(
                {"content": content, "agent": payload.agent}
            )
            processed_by = "ApprovalAgent"

        else:
            return {"status": "ignored", "reason": f"Unknown message type: {message_type}"}

        # Log the webhook processing
        await db_client.log_agent_action(
            request_id=content.get("request_id", "unknown"),
            agent_name="WebhookRouter",
            action=f"routed_to_{processed_by}",
            output={
                "message_type": message_type,
                "processed_by": processed_by,
                "result": result,
            },
        )

        return {
            "status": "processed",
            "processed_by": processed_by,
            "result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook."""
    return {"status": "ok", "service": "ProcureFlow AI Webhook"}