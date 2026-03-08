"""
WebSocket Routes

Real-time communication endpoints.
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from app.core.config import settings
from app.core.websocket import manager, WebSocketMessage

logger = logging.getLogger("bookapi.websocket")

ws_router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def get_user_from_token(token: str) -> Optional[dict]:
    """Validate JWT token and return user info."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "uuid": payload.get("uuid", user_id)}
    except JWTError:
        return None


@ws_router.websocket("/connect")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(..., description="JWT access token")
):
    """
    Main WebSocket endpoint for real-time communication.

    Connect with: ws://localhost:8000/ws/connect?token=<jwt_token>

    Message format:
    ```json
    {
        "action": "join_room" | "leave_room" | "send_message" | "typing" | "ping",
        "room_id": "optional_room_id",
        "data": {}
    }
    ```
    """
    # Validate token
    user_info = await get_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = user_info["user_id"]

    try:
        await manager.connect(websocket, user_id)

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "ping":
                    # Health check / keep alive
                    await manager.send_personal_message(
                        WebSocketMessage(type="pong", data={}),
                        user_id
                    )

                elif action == "join_room":
                    room_id = message.get("room_id")
                    if room_id:
                        await manager.join_room(user_id, room_id)
                        await manager.send_personal_message(
                            WebSocketMessage(
                                type="room_joined",
                                data={"room_id": room_id}
                            ),
                            user_id
                        )

                elif action == "leave_room":
                    room_id = message.get("room_id")
                    if room_id:
                        await manager.leave_room(user_id, room_id)
                        await manager.send_personal_message(
                            WebSocketMessage(
                                type="room_left",
                                data={"room_id": room_id}
                            ),
                            user_id
                        )

                elif action == "send_message":
                    room_id = message.get("room_id")
                    content = message.get("data", {}).get("content", "")

                    if room_id:
                        # Send to room
                        await manager.send_to_room(
                            room_id,
                            WebSocketMessage(
                                type="chat_message",
                                data={
                                    "from_user": user_id,
                                    "room_id": room_id,
                                    "content": content
                                }
                            )
                        )
                    else:
                        # Broadcast to all
                        await manager.broadcast(
                            WebSocketMessage(
                                type="chat_message",
                                data={
                                    "from_user": user_id,
                                    "content": content
                                }
                            ),
                            exclude_user=user_id
                        )

                elif action == "typing":
                    room_id = message.get("room_id")
                    if room_id:
                        await manager.send_to_room(
                            room_id,
                            WebSocketMessage(
                                type="user_typing",
                                data={"user_id": user_id, "room_id": room_id}
                            ),
                            exclude_user=user_id
                        )

                elif action == "get_online_users":
                    online_users = manager.get_online_users()
                    await manager.send_personal_message(
                        WebSocketMessage(
                            type="online_users",
                            data={"users": online_users}
                        ),
                        user_id
                    )

                elif action == "get_room_users":
                    room_id = message.get("room_id")
                    if room_id:
                        room_users = manager.get_room_users(room_id)
                        await manager.send_personal_message(
                            WebSocketMessage(
                                type="room_users",
                                data={"room_id": room_id, "users": room_users}
                            ),
                            user_id
                        )

                else:
                    # Unknown action
                    await manager.send_personal_message(
                        WebSocketMessage(
                            type="error",
                            data={"message": f"Unknown action: {action}"}
                        ),
                        user_id
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    WebSocketMessage(
                        type="error",
                        data={"message": "Invalid JSON format"}
                    ),
                    user_id
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify others about disconnection
        await manager.broadcast(
            WebSocketMessage(
                type="user_disconnected",
                data={"user_id": user_id}
            )
        )


@ws_router.websocket("/notifications")
async def notifications_endpoint(
        websocket: WebSocket,
        token: str = Query(..., description="JWT access token")
):
    """
    WebSocket endpoint for receiving real-time notifications.

    This is a read-only endpoint - the server pushes notifications to the client.
    """
    user_info = await get_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = user_info["user_id"]

    try:
        await manager.connect(websocket, user_id)

        # Keep connection alive
        while True:
            # Just keep the connection open for receiving server pushes
            data = await websocket.receive_text()

            # Only respond to ping messages
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    await manager.send_personal_message(
                        WebSocketMessage(type="pong", data={}),
                        user_id
                    )
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
