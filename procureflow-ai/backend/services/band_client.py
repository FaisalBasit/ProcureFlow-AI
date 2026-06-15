"""
Band SDK wrapper for ProcureFlow AI.
Handles room creation, message sending, and context exchange.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

BAND_API_KEY = os.getenv("BAND_API_KEY")
BAND_ROOM_ID = os.getenv("BAND_ROOM_ID")


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
        self.base_url = "https://api.bandprotocol.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_message(self, content: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Send a structured message to the Band room."""
        payload = {
            "room_id": self.room_id,
            "agent": agent_name,
            "content": content,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
            )
        if resp.status_code != 200:
            raise BandClientError(f"Failed to send message: {resp.text}")
        return resp.json()

    async def get_messages(self, limit: int = 50) -> list:
        """Retrieve recent messages from the Band room."""
        params = {"room_id": self.room_id, "limit": limit}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/messages",
                headers=self.headers,
                params=params,
            )
        if resp.status_code != 200:
            raise BandClientError(f"Failed to get messages: {resp.text}")
        return resp.json().get("messages", [])

    async def get_room_context(self) -> Dict[str, Any]:
        """Get full room context including all messages and state."""
        messages = await self.get_messages(limit=100)
        return {"room_id": self.room_id, "messages": messages}

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