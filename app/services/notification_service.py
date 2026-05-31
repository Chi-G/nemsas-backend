import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import WebSocket
import redis.asyncio as redis
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.pubsub = None
        # In-memory mapping of websocket connections
        # Format: { websocket: {"user_id": int, "state_id": int | None, "user_type": str} }
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        self.channel_name = "incidents"
        self._listener_task = None

    async def connect_redis(self):
        """Connect to Redis and start the pubsub listener."""
        if not self.redis:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel_name)
            self._listener_task = asyncio.create_task(self._listen_for_messages())
            logger.info("Connected to Redis and subscribed to incidents channel.")

    async def disconnect_redis(self):
        """Disconnect from Redis."""
        if self._listener_task:
            self._listener_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def connect(self, websocket: WebSocket, user: User):
        """Accept a websocket connection and store user metadata."""
        await websocket.accept()
        self.active_connections[websocket] = {
            "user_id": user.id,
            "state_id": user.state_id,
            "user_type": user.user_type
        }
        logger.info(f"User {user.id} connected to websockets. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a websocket connection."""
        if websocket in self.active_connections:
            user_id = self.active_connections[websocket]["user_id"]
            del self.active_connections[websocket]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def publish_incident(self, incident_data: Dict[str, Any]):
        """Publish an incident to the Redis channel."""
        try:
            if not self.redis:
                await self.connect_redis()
            
            message = json.dumps(incident_data)
            if self.redis:
                await self.redis.publish(self.channel_name, message)
        except Exception as e:
            logger.warning(f"Could not publish incident update to Redis: {e}. Pub-sub notification skipped.")

    async def _listen_for_messages(self):
        """Listen for messages from Redis and route them to appropriate websockets."""
        try:
            if self.pubsub:
                async for message in self.pubsub.listen():
                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        await self._broadcast_to_clients(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in redis listener: {e}")

    async def _broadcast_to_clients(self, incident_data: Dict[str, Any]):
        """
        Broadcast the incident to connected clients based on their roles.
        Global roles see everything.
        State roles only see incidents matching their state_id.
        """
        incident_state_id = incident_data.get("state_id")
        global_roles = {"SUPERADMINISTRATOR", "NEMSASADMIN", "NATIONALVIEWER", "NEMSASUSER"}
        
        dead_connections = []

        for websocket, meta in self.active_connections.items():
            try:
                # Determine if user should receive this message
                should_send = False
                
                if meta["user_type"] in global_roles:
                    should_send = True
                elif meta["state_id"] is not None and incident_state_id is not None:
                    if int(meta["state_id"]) == int(incident_state_id):
                        should_send = True
                        
                if should_send:
                    await websocket.send_json(incident_data)
            except Exception as e:
                logger.error(f"Failed to send to websocket, marking as dead: {e}")
                dead_connections.append(websocket)
                
        # Cleanup dead connections
        for ws in dead_connections:
            self.disconnect(ws)

notification_service = NotificationService()
