"""
SHA-256 audit packet generator for ProcureFlow AI.
Seals the final decision with a tamper-evident hash.
"""

import json
import hashlib
from typing import Dict, Any
from datetime import datetime


def generate_audit_packet(
    request_id: str,
    vendor_name: str,
    amount: float,
    category: str,
    justification: str,
    risk_report: Dict[str, Any],
    policy_verdict: Dict[str, Any],
    approval_summary: str,
    human_decision: str,
    signed_by: str,
) -> Dict[str, Any]:
    """
    Generate a complete audit packet with SHA-256 hash seal.
    """
    packet = {
        "request_id": request_id,
        "vendor_name": vendor_name,
        "amount": amount,
        "category": category,
        "justification": justification,
        "risk_report": risk_report,
        "policy_verdict": policy_verdict,
        "approval_summary": approval_summary,
        "human_decision": human_decision,
        "signed_by": signed_by,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Compute SHA-256 hash of the packet contents
    packet_json = json.dumps(packet, sort_keys=True, default=str)
    audit_hash = hashlib.sha256(packet_json.encode("utf-8")).hexdigest()

    packet["audit_hash"] = audit_hash
    packet["hash_algorithm"] = "SHA-256"

    return packet


def verify_audit_packet(packet: Dict[str, Any]) -> bool:
    """
    Verify the integrity of an audit packet by re-computing its hash.
    """
    stored_hash = packet.pop("audit_hash", None)
    hash_algorithm = packet.pop("hash_algorithm", None)

    if not stored_hash:
        return False

    packet_json = json.dumps(packet, sort_keys=True, default=str)
    computed_hash = hashlib.sha256(packet_json.encode("utf-8")).hexdigest()

    # Restore fields
    packet["audit_hash"] = stored_hash
    packet["hash_algorithm"] = hash_algorithm

    return computed_hash == stored_hash