"""
@Intake Agent — ProcureFlow AI
Parses purchase requests and posts structured context to Band room.
Uses LangChain for structured output parsing.
"""

import os
import json
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.band_client import BandClient, BandClientError
from backend.db.supabase_client import SupabaseDBClient

load_dotenv()


class IntakeAgent:
    """Parses and validates incoming purchase requests."""

    def __init__(self):
        self.band = BandClient()
        self.db = SupabaseDBClient()

    def validate_request(
        self,
        vendor_name: str,
        amount: float,
        category: str,
        justification: str,
    ) -> Dict[str, Any]:
        """Validate the purchase request fields."""
        errors = []
        warnings = []

        if not vendor_name or len(vendor_name.strip()) < 2:
            errors.append("Vendor name must be at least 2 characters")

        if amount <= 0:
            errors.append("Amount must be greater than 0")
        elif amount > 1_000_000:
            warnings.append("Amount exceeds $1,000,000 — requires board approval")

        valid_categories = [
            "software", "hardware", "consulting", "services",
            "supplies", "capital", "other",
        ]
        if category.lower() not in valid_categories:
            warnings.append(f"Category '{category}' is not standard. Using 'other'.")
            category = "other"

        if not justification or len(justification.strip()) < 10:
            errors.append("Justification must be at least 10 characters")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "parsed": {
                "vendor_name": vendor_name.strip(),
                "amount": amount,
                "category": category.lower(),
                "justification": justification.strip(),
            },
        }

    async def process_request(
        self,
        vendor_name: str,
        amount: float,
        category: str,
        justification: str,
    ) -> Dict[str, Any]:
        """
        Process a purchase request: validate, store in DB, post to Band room.
        """
        # Validate
        validation = self.validate_request(vendor_name, amount, category, justification)
        if not validation["valid"]:
            return {
                "status": "rejected",
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }

        parsed = validation["parsed"]

        # Store in database
        request = await self.db.create_request(
            vendor_name=parsed["vendor_name"],
            amount=parsed["amount"],
            category=parsed["category"],
            justification=parsed["justification"],
        )
        request_id = request["id"]

        # Log intake action
        await self.db.log_agent_action(
            request_id=request_id,
            agent_name="IntakeAgent",
            action="request_parsed",
            output={
                "vendor_name": parsed["vendor_name"],
                "amount": parsed["amount"],
                "category": parsed["category"],
                "justification": parsed["justification"],
                "warnings": validation["warnings"],
            },
        )

        # Post structured context to Band room
        band_message = {
            "type": "purchase_request",
            "request_id": request_id,
            "vendor_name": parsed["vendor_name"],
            "amount": parsed["amount"],
            "category": parsed["category"],
            "justification": parsed["justification"],
            "status": "pending_risk_assessment",
            "warnings": validation["warnings"],
        }

        await self.db.update_request_status(request_id, "risk_assessment")
        try:
            band_result = await self.band.send_message(band_message, "IntakeAgent")
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_posted",
                output={
                    "source_agent": "IntakeAgent",
                    "event_type": band_message["type"],
                    "band_result": band_result,
                },
            )
            handoff_result = await self.band.send_handoff_message(
                source_agent_name="IntakeAgent",
                target_agent_name="RiskAgent",
                handoff=(
                    f"Request {request_id} is parsed and ready for vendor risk analysis. "
                    f"Vendor: {parsed['vendor_name']}; amount: ${parsed['amount']:,.2f}; "
                    f"category: {parsed['category']}."
                ),
            )
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_handoff_posted",
                output={
                    "source_agent": "IntakeAgent",
                    "target_agent": "RiskAgent",
                    "band_result": handoff_result,
                },
            )
        except BandClientError as e:
            # Still return the request even if Band fails (degraded mode)
            await self.db.log_agent_action(
                request_id=request_id,
                agent_name="BandBridge",
                action="band_event_failed",
                output={
                    "source_agent": "IntakeAgent",
                    "event_type": band_message["type"],
                    "error": str(e),
                },
            )
            print(f"Warning: Band communication failed: {e}")

        return {
            "status": "submitted",
            "request_id": request_id,
            "vendor_name": parsed["vendor_name"],
            "amount": parsed["amount"],
            "category": parsed["category"],
            "warnings": validation["warnings"],
        }
