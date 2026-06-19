"""
Supabase client for ProcureFlow AI.
Handles all database operations — requests, agent_logs, decisions.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class SupabaseClientError(Exception):
    pass


class SupabaseDBClient:
    """Client for Supabase database operations."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        if not self.url or not self.key:
            raise SupabaseClientError("SUPABASE_URL and SUPABASE_KEY must be set")
        self.client: Client = create_client(self.url, self.key)

    def _json_safe(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Return a JSONB-safe object without turning it into a JSON string."""
        return json.loads(json.dumps(value, default=str))

    def _normalize_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        output = log.get("output")
        if isinstance(output, str):
            try:
                log["output"] = json.loads(output)
            except json.JSONDecodeError:
                log["output"] = {"raw": output}
        return log

    def _status_from_activity(
        self,
        request: Dict[str, Any],
        logs: List[Dict[str, Any]],
        decision: Optional[Dict[str, Any]],
    ) -> str:
        """Infer the request status from the durable audit trail."""
        if decision:
            return "approved" if decision.get("human_approved") else "rejected"

        current_status = request.get("status", "pending")
        for log in reversed(logs):
            agent_name = log.get("agent_name")
            action = log.get("action")
            output = log.get("output") or {}

            if agent_name == "ApprovalAgent" and action == "decision_finalized":
                human_decision = output.get("human_decision")
                if human_decision in ("approved", "rejected"):
                    return human_decision
                return current_status

            if agent_name == "ApprovalAgent" and action == "approval_summary_generated":
                return "awaiting_approval"

            if agent_name == "PolicyAgent" and action == "policy_check_complete":
                verdict = output.get("verdict")
                if verdict == "rejected":
                    return "rejected_by_policy"
                if output.get("human_visible", True):
                    return "flagged_for_review" if verdict == "flagged" else "pending_approval"
                return current_status

            if agent_name == "RiskAgent" and action == "risk_analysis_complete":
                return "policy_check"

            if agent_name == "IntakeAgent" and action == "request_parsed":
                return "risk_assessment"

        return current_status

    async def reconcile_request_status(
        self,
        request: Dict[str, Any],
        logs: Optional[List[Dict[str, Any]]] = None,
        decision: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """Repair stale statuses by deriving the truth from logs and decisions."""
        request_id = request["id"]
        normalized_logs = logs if logs is not None else await self.get_agent_logs(request_id)
        existing_decision = decision if decision is not None else await self.get_decision(request_id)
        effective_status = self._status_from_activity(request, normalized_logs, existing_decision)

        if persist and effective_status != request.get("status"):
            updated = await self.update_request_status(request_id, effective_status)
            if updated:
                return updated

        return {**request, "status": effective_status}

    # --- Requests ---

    async def create_request(
        self,
        vendor_name: str,
        amount: float,
        category: str,
        justification: str,
    ) -> Dict[str, Any]:
        """Insert a new purchase request."""
        data = {
            "vendor_name": vendor_name,
            "amount": amount,
            "category": category,
            "justification": justification,
            "status": "pending",
        }
        result = self.client.table("requests").insert(data).execute()
        if not result.data:
            raise SupabaseClientError("Failed to create request")
        return result.data[0]

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a single request by ID."""
        result = self.client.table("requests").select("*").eq("id", request_id).execute()
        return result.data[0] if result.data else None

    async def update_request_status(self, request_id: str, status: str) -> Dict[str, Any]:
        """Update request status."""
        result = (
            self.client.table("requests")
            .update({
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", request_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_requests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List requests with optional status filter."""
        result = self.client.table("requests").select("*").order("created_at", desc=True).execute()
        reconciled = [
            await self.reconcile_request_status(request)
            for request in result.data
        ]
        if status:
            return [request for request in reconciled if request.get("status") == status]
        return reconciled

    # --- Agent Logs ---

    async def log_agent_action(
        self,
        request_id: str,
        agent_name: str,
        action: str,
        output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Log an agent's action for a request."""
        data = {
            "request_id": request_id,
            "agent_name": agent_name,
            "action": action,
            "output": self._json_safe(output),
        }
        result = self.client.table("agent_logs").insert(data).execute()
        return self._normalize_log(result.data[0]) if result.data else None

    async def get_agent_logs(self, request_id: str) -> List[Dict[str, Any]]:
        """Get all agent logs for a request."""
        result = (
            self.client.table("agent_logs")
            .select("*")
            .eq("request_id", request_id)
            .order("created_at")
            .execute()
        )
        return [self._normalize_log(log) for log in result.data]

    # --- Decisions ---

    async def record_decision(
        self,
        request_id: str,
        human_approved: bool,
        audit_hash: str,
        signed_by: str,
    ) -> Dict[str, Any]:
        """Record a human decision and audit hash."""
        data = {
            "request_id": request_id,
            "human_approved": human_approved,
            "audit_hash": audit_hash,
            "signed_by": signed_by,
        }
        result = self.client.table("decisions").insert(data).execute()
        return result.data[0] if result.data else None

    async def get_decision(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the decision record for a request."""
        result = (
            self.client.table("decisions")
            .select("*")
            .eq("request_id", request_id)
            .execute()
        )
        return result.data[0] if result.data else None
