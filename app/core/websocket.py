"""
WebSocket Manager

Manages WebSocket connections for real-time communication.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger("bookapi.websocket")


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str
    data: dict
    timestamp: str = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**kwargs)


class ConnectionManager:
    """
    Manages WebSocket connections.

    Supports:
    - Multiple connections per user
    - Room-based messaging (e.g., book discussions)
    - Broadcast to all users
    - Private messaging
    """

    def __init__(self):
        # user_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # room_id -> set of user_ids
        self.rooms: Dict[str, Set[str]] = {}
        # websocket -> user_id mapping
        self.connection_user_map: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        self.connection_user_map[websocket] = user_id

        logger.info(f"User {user_id} connected via WebSocket")

        # Notify user of successful connection
        await self.send_personal_message(
            WebSocketMessage(
                type="connection",
                data={"status": "connected", "user_id": user_id}
            ),
            user_id
        )

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        user_id = self.connection_user_map.get(websocket)

        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Remove user from all rooms
                for room_id in list(self.rooms.keys()):
                    if user_id in self.rooms[room_id]:
                        self.rooms[room_id].remove(user_id)
                        if not self.rooms[room_id]:
                            del self.rooms[room_id]

        if websocket in self.connection_user_map:
            del self.connection_user_map[websocket]

        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: WebSocketMessage, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            message_json = message.model_dump_json()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

    async def broadcast(self, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast a message to all connected users."""
        message_json = message.model_dump_json()

        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            for connection in connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")

    async def join_room(self, user_id: str, room_id: str):
        """Add a user to a room."""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(user_id)
        logger.info(f"User {user_id} joined room {room_id}")

        # Notify room members
        await self.send_to_room(
            room_id,
            WebSocketMessage(
                type="room_event",
                data={"event": "user_joined", "user_id": user_id, "room_id": room_id}
            ),
            exclude_user=user_id
        )

    async def leave_room(self, user_id: str, room_id: str):
        """Remove a user from a room."""
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            self.rooms[room_id].remove(user_id)

            if not self.rooms[room_id]:
                del self.rooms[room_id]

            logger.info(f"User {user_id} left room {room_id}")

            # Notify remaining room members
            await self.send_to_room(
                room_id,
                WebSocketMessage(
                    type="room_event",
                    data={"event": "user_left", "user_id": user_id, "room_id": room_id}
                )
            )

    async def send_to_room(
            self,
            room_id: str,
            message: WebSocketMessage,
            exclude_user: Optional[str] = None
    ):
        """Send a message to all users in a room."""
        if room_id not in self.rooms:
            return

        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue

            await self.send_personal_message(message, user_id)

    def get_online_users(self) -> List[str]:
        """Get list of online user IDs."""
        return list(self.active_connections.keys())

    def get_room_users(self, room_id: str) -> List[str]:
        """Get list of users in a room."""
        return list(self.rooms.get(room_id, set()))

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is online."""
        return user_id in self.active_connections


# Global connection manager instance
manager = ConnectionManager()
