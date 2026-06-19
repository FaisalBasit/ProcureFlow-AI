"""
Procurement routes for ProcureFlow AI.
Handles purchase request submission, status checking, and approval.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.intake_agent import IntakeAgent
from agents.risk_agent import RiskAgent
from agents.policy_agent import PolicyAgent
from agents.approval_agent import ApprovalAgent
from backend.db.supabase_client import SupabaseDBClient

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


class PurchaseRequest(BaseModel):
    vendor_name: str = Field(..., min_length=2, description="Vendor name")
    amount: float = Field(..., gt=0, description="Purchase amount in USD")
    category: str = Field(..., description="Category: software/hardware/consulting/services/supplies/capital/other")
    justification: str = Field(..., min_length=10, description="Business justification")


class ApprovalDecision(BaseModel):
    request_id: str = Field(..., description="Request UUID")
    approved: bool = Field(..., description="Approve or reject")
    signed_by: str = Field(..., min_length=2, description="Approver name")


# Agent instances (singletons for route handlers)
intake_agent = IntakeAgent()
risk_agent = RiskAgent()
policy_agent = PolicyAgent()
approval_agent = ApprovalAgent()
db_client = SupabaseDBClient()


@router.post("/submit")
async def submit_purchase_request(req: PurchaseRequest):
    """Submit a new purchase request. Starts the full agent workflow."""
    try:
        result = await intake_agent.process_request(
            vendor_name=req.vendor_name,
            amount=req.amount,
            category=req.category,
            justification=req.justification,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-and-process")
async def submit_and_process(req: PurchaseRequest):
    """
    Submit a purchase request and run the full agent pipeline
    (Intake → RiskAgent → PolicyAgent → ApprovalAgent)
    Useful for testing and demo purposes.
    """
    try:
        # Step 1: Intake
        intake_result = await intake_agent.process_request(
            vendor_name=req.vendor_name,
            amount=req.amount,
            category=req.category,
            justification=req.justification,
        )
        if intake_result["status"] == "rejected":
            return intake_result

        request_id = intake_result["request_id"]

        # Step 2: Risk Assessment
        risk_result = await risk_agent.analyze_request(request_id)

        # Step 3: Policy Check
        policy_result = await policy_agent.check_compliance(request_id)

        # Step 4: Prepare for Approval (if human-visible)
        approval_result = None
        if policy_result.get("human_visible", True):
            approval_result = await approval_agent.prepare_for_approval(request_id)

        return {
            "request_id": request_id,
            "intake": intake_result,
            "risk_assessment": risk_result,
            "policy_check": policy_result,
            "approval": approval_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests")
async def list_requests(status: Optional[str] = None):
    """List all purchase requests, optionally filtered by status."""
    try:
        requests = await db_client.list_requests(status=status)
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}")
async def get_request(request_id: str):
    """Get details of a specific purchase request."""
    try:
        request = await db_client.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        logs = await db_client.get_agent_logs(request_id)
        decision = await db_client.get_decision(request_id)
        request = await db_client.reconcile_request_status(
            request,
            logs=logs,
            decision=decision,
        )

        return {
            "request": request,
            "agent_logs": logs,
            "decision": decision,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/audit")
async def get_audit_packet(request_id: str):
    """Get the complete audit packet for a finalized request."""
    try:
        request = await db_client.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        decision = await db_client.get_decision(request_id)
        if not decision:
            raise HTTPException(status_code=404, detail="No decision recorded yet")

        logs = await db_client.get_agent_logs(request_id)

        return {
            "request": request,
            "decision": decision,
            "agent_logs": logs,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_request(decision: ApprovalDecision):
    """Submit a human approval or rejection decision."""
    try:
        result = await approval_agent.process_human_decision(
            request_id=decision.request_id,
            approved=decision.approved,
            signed_by=decision.signed_by,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/status")
async def get_request_status(request_id: str):
    """Get the current status of a purchase request."""
    try:
        request = await db_client.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        logs = await db_client.get_agent_logs(request_id)
        decision = await db_client.get_decision(request_id)
        request = await db_client.reconcile_request_status(
            request,
            logs=logs,
            decision=decision,
        )

        agent_statuses = {}
        for log in logs:
            agent_statuses[log["agent_name"]] = log["action"]

        return {
            "request_id": request_id,
            "status": request["status"],
            "vendor_name": request["vendor_name"],
            "amount": request["amount"],
            "agents": agent_statuses,
            "approved": decision["human_approved"] if decision else None,
            "audit_hash": decision["audit_hash"] if decision else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
