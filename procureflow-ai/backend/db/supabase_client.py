"""
Supabase client for ProcureFlow AI.
Handles all database operations — requests, agent_logs, decisions.
"""

import os
import json
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
            .update({"status": status, "updated_at": "now()"})
            .eq("id", request_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_requests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List requests with optional status filter."""
        query = self.client.table("requests").select("*")
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).execute()
        return result.data

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
            "output": json.dumps(output),
        }
        result = self.client.table("agent_logs").insert(data).execute()
        return result.data[0] if result.data else None

    async def get_agent_logs(self, request_id: str) -> List[Dict[str, Any]]:
        """Get all agent logs for a request."""
        result = (
            self.client.table("agent_logs")
            .select("*")
            .eq("request_id", request_id)
            .order("created_at")
            .execute()
        )
        return result.data

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