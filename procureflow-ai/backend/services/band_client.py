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


class BandClientError(Exception):
    pass


class BandClient:
    """Client for interacting with Band rooms and agents."""

    def __init__(self, api_key: Optional[str] = None, room_id: Optional[str] = None):
        self.api_key = api_key or BAND_API_KEY
        self.room_id = room_id or BAND_ROOM_ID
        if not self.api_key:
            raise BandClientError("BAND_API_KEY is not set")
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

    async def send_message(self, content: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Send a structured collaboration event to the configured Band chat."""
        return await self.send_event(content, agent_name)

    async def send_event(self, content: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Post an informational event to Band's Agent API."""
        payload = {
            "event": {
                "content": self._event_content(content, agent_name),
                "message_type": "task",
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
        params = {"status": "all", "page_size": limit}
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

    async def get_room_context(self) -> Dict[str, Any]:
        """Get full room context including all messages and state."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/chats/{self.room_id}/context",
                    headers=self._headers_for_agent("IntakeAgent"),
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
        return {"room_id": self.room_id, "context": data}

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
