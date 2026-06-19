"""
Band SDK wrapper for ProcureFlow AI.
Handles room creation, message sending, and context exchange.
"""

import os
import json
import re
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

BAND_API_KEY = os.getenv("BAND_API_KEY")
BAND_ROOM_ID = os.getenv("BAND_ROOM_ID")
BAND_BASE_URL = os.getenv("BAND_BASE_URL", "https://app.band.ai/api/v1/agent")

AGENT_DISPLAY_NAMES = {
    "IntakeAgent": "ProcureFlow Intake Agent",
    "RiskAgent": "ProcureFlow Risk Agent",
    "PolicyAgent": "ProcureFlow Policy Agent",
    "FeatherlessReviewAgent": "ProcureFlow Featherless Review Agent",
    "ApprovalAgent": "ProcureFlow Approval Agent",
}


class BandClientError(Exception):
    pass


class BandClient:
    """Client for interacting with Band rooms and agents."""

    def __init__(self, api_key: Optional[str] = None, room_id: Optional[str] = None):
        self.api_key = (
            api_key
            or BAND_API_KEY
            or os.getenv("BAND_INTAKE_API_KEY")
            or os.getenv("BAND_RISK_API_KEY")
            or os.getenv("BAND_POLICY_API_KEY")
            or os.getenv("BAND_FEATHERLESS_REVIEW_API_KEY")
            or os.getenv("BAND_FEATHERLESS_API_KEY")
            or os.getenv("BAND_APPROVAL_API_KEY")
        )
        self.room_id = room_id or BAND_ROOM_ID
        if not self.api_key:
            raise BandClientError(
                "BAND_API_KEY or per-agent Band API keys must be set "
                "(BAND_INTAKE_API_KEY, BAND_RISK_API_KEY, BAND_POLICY_API_KEY, "
                "BAND_FEATHERLESS_REVIEW_API_KEY, BAND_APPROVAL_API_KEY)"
            )
        if not self.room_id:
            raise BandClientError("BAND_ROOM_ID is not set")
        self.base_url = BAND_BASE_URL.rstrip("/")

    def _headers_for_agent(self, agent_name: str) -> Dict[str, str]:
        api_key = self._api_key_for_agent(agent_name)
        return {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def _api_key_for_agent(self, agent_name: str) -> str:
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", agent_name).upper()
        short_name = snake_name.replace("_AGENT", "")
        return (
            os.getenv(f"BAND_{snake_name}_API_KEY")
            or os.getenv(f"BAND_{short_name}_API_KEY")
            or self.api_key
        )

    def _event_content(self, content: Dict[str, Any], agent_name: str) -> str:
        message_type = content.get("type", "agent_event").replace("_", " ")
        request_id = content.get("request_id", "unknown")
        status = content.get("status", "updated")
        return f"{agent_name} {message_type} for request {request_id}: {status}"

    def _message_type(self, content: Dict[str, Any]) -> str:
        event_type = content.get("type", "task")
        if event_type in (
            "risk_report",
            "policy_verdict",
            "featherless_review",
            "approval_summary",
            "final_decision",
        ):
            return "tool_result"
        if event_type in ("error", "band_error"):
            return "error"
        if event_type in ("agent_thought", "thought"):
            return "thought"
        return "task"

    async def get_agent_profile(self, agent_name: str = "IntakeAgent") -> Dict[str, Any]:
        """Validate one agent API key and return Band's agent profile response."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/me",
                    headers=self._headers_for_agent(agent_name),
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                f"Band rejected {agent_name} with 403 Forbidden. "
                "Use the one-time Agent API key from an External Agent."
            )
        if resp.status_code == 401:
            raise BandClientError(
                f"Band rejected {agent_name} with 401 Unauthorized. "
                "Check that the Agent API key was copied correctly."
            )
        if resp.status_code != 200:
            raise BandClientError(
                f"Failed to validate {agent_name}: {resp.status_code} - {resp.text}"
            )
        return resp.json()

    async def get_participants(self, agent_name: str = "IntakeAgent") -> list:
        """List participants in the configured Band chat room."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/chats/{self.room_id}/participants",
                    headers=self._headers_for_agent(agent_name),
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                f"Band rejected participant lookup for {agent_name} with 403 Forbidden. "
                "Add that External Agent as a participant in BAND_ROOM_ID."
            )
        if resp.status_code != 200:
            raise BandClientError(f"Failed to get participants: {resp.status_code} - {resp.text}")
        return resp.json().get("data", [])

    async def send_message(self, content: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Send a structured collaboration event to the configured Band chat."""
        return await self.send_event(content, agent_name)

    def _participant_for_agent(
        self,
        participants: list,
        agent_name: str,
    ) -> Optional[Dict[str, Any]]:
        target_name = AGENT_DISPLAY_NAMES.get(agent_name, agent_name)
        for participant in participants:
            if participant.get("name") == target_name:
                return participant
        return None

    async def send_handoff_message(
        self,
        source_agent_name: str,
        target_agent_name: str,
        handoff: str,
    ) -> Dict[str, Any]:
        """Send a directed @mention message from one Band agent to the next."""
        participants = await self.get_participants(source_agent_name)
        target = self._participant_for_agent(participants, target_agent_name)
        if not target:
            raise BandClientError(
                f"Cannot hand off to {target_agent_name}; add {AGENT_DISPLAY_NAMES.get(target_agent_name, target_agent_name)} "
                f"as a participant in BAND_ROOM_ID."
            )

        mention = {
            "id": target["id"],
            "handle": target["handle"],
            "name": target["name"],
        }
        payload = {
            "message": {
                "content": f"@{target['handle']} {handoff}",
                "mentions": [mention],
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chats/{self.room_id}/messages",
                    headers=self._headers_for_agent(source_agent_name),
                    json=payload,
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                f"Band rejected handoff from {source_agent_name} to {target_agent_name} with 403 Forbidden. "
                "Make sure both agents are participants in BAND_ROOM_ID."
            )
        if resp.status_code not in (200, 201):
            raise BandClientError(
                f"Failed to send Band handoff: {resp.status_code} - {resp.text}"
            )
        return resp.json() if resp.content else {"status": "created"}

    async def send_event(self, content: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Post an informational event to Band's Agent API."""
        payload = {
            "event": {
                "content": self._event_content(content, agent_name),
                "message_type": self._message_type(content),
                "metadata": {
                    "agent_name": agent_name,
                    "event_type": content.get("type", "agent_event"),
                    **content,
                },
            }
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chats/{self.room_id}/events",
                    headers=self._headers_for_agent(agent_name),
                    json=payload,
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                "Band rejected the event with 403 Forbidden. "
                "Use an Agent API key for an agent that is a participant in BAND_ROOM_ID."
            )
        if resp.status_code not in (200, 201):
            raise BandClientError(f"Failed to send Band event: {resp.status_code} - {resp.text}")
        if resp.content:
            return resp.json()
        return {"status": "created"}

    async def get_messages(self, limit: int = 50) -> list:
        """Retrieve recent messages from the Band chat for diagnostics."""
        params = {"status": "all", "limit": limit}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/chats/{self.room_id}/messages",
                    headers=self._headers_for_agent("IntakeAgent"),
                    params=params,
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                "Band rejected the messages request with 403 Forbidden. "
                "Use an Agent API key for an agent that is a participant in BAND_ROOM_ID."
            )
        if resp.status_code != 200:
            raise BandClientError(f"Failed to get messages: {resp.text}")
        data = resp.json()
        return data.get("data") or data.get("messages", [])

    async def get_room_context(self, agent_name: str = "IntakeAgent") -> Dict[str, Any]:
        """Get full room context including all messages and state."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/chats/{self.room_id}/context",
                    headers=self._headers_for_agent(agent_name),
                    timeout=10.0,
                )
        except httpx.ConnectError as e:
            raise BandClientError(f"Connection failed to Band API: {e}")
        except httpx.TimeoutException as e:
            raise BandClientError(f"Timeout connecting to Band API: {e}")
        except Exception as e:
            raise BandClientError(f"Unexpected error calling Band API: {e}")

        if resp.status_code == 403:
            raise BandClientError(
                "Band rejected the context request with 403 Forbidden. "
                "Use an Agent API key for an agent that is a participant in BAND_ROOM_ID."
            )
        if resp.status_code != 200:
            raise BandClientError(f"Failed to get room context: {resp.text}")
        data = resp.json()
        return {"room_id": self.room_id, "agent_name": agent_name, "context": data}

    async def send_task_result(self, task_id: str, result: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Send the result of a completed agent task back to the room."""
        payload = {
            "task_id": task_id,
            "agent": agent_name,
            "result": result,
        }
        return await self.send_message(payload, agent_name)

    async def wait_for_agent_response(self, agent_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Poll for a response from a specific agent."""
        import asyncio
        for _ in range(timeout):
            messages = await self.get_messages(limit=10)
            for msg in messages:
                if msg.get("agent") == agent_name:
                    return msg
            await asyncio.sleep(1)
        return None
