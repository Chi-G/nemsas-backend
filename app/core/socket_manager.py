import socketio
import time
from typing import Any, Dict, List, Optional
from collections import deque

# Create a Socket.IO ASYNC server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# In-memory buffer for recent events: { "state-15": deque([...], maxlen=50) }
EVENT_BUFFER: Dict[str, deque] = {}

class SocketManager:
    @staticmethod
    def _add_to_buffer(room: str, payload: Dict[str, Any]):
        if room not in EVENT_BUFFER:
            EVENT_BUFFER[room] = deque(maxlen=50)
        
        # Add timestamp to payload for sync tracking
        payload["timestamp"] = time.time()
        EVENT_BUFFER[room].append(payload)

    @staticmethod
    async def join_state_group(sid: str, state_id: int):
        room = f"state-{state_id}"
        print(f"[Socket] User {sid} joining room {room}")
        await sio.enter_room(sid, room)
        await sio.emit("GroupJoined", {"stateId": state_id, "room": room}, to=sid)

    @staticmethod
    async def broadcast_incident_update(state_id: int, payload: Dict[str, Any]):
        room = f"state-{state_id}"
        
        # Add to buffer before broadcasting
        SocketManager._add_to_buffer(room, payload)
        
        print(f"[Socket] Broadcasting update to room {room}: {payload}")
        await sio.emit("ReceiveMessage", payload, room=room)

    @staticmethod
    async def sync_missed_events(sid: str, state_id: int, last_timestamp: float):
        """
        Sends missed events to a client based on their last seen timestamp.
        """
        room = f"state-{state_id}"
        if room in EVENT_BUFFER:
            missed = [msg for msg in EVENT_BUFFER[room] if msg["timestamp"] > last_timestamp]
            if missed:
                print(f"[Socket] Sending {len(missed)} missed events to {sid}")
                for msg in missed:
                    await sio.emit("ReceiveMessage", msg, to=sid)

# Event Handlers
@sio.event
async def connect(sid, environ):
    print(f"[Socket] Client connected: {sid}")

@sio.on("JoinStateGroup")
async def handle_join_state_group(sid, data):
    state_id = data.get("state_id") or data.get("stateId")
    last_timestamp = data.get("lastTimestamp") # Optional: for immediate sync on join
    
    if state_id:
        await SocketManager.join_state_group(sid, state_id)
        if last_timestamp:
            await SocketManager.sync_missed_events(sid, state_id, last_timestamp)
    else:
        await sio.emit("GroupJoinFailed", {"error": "stateId is required"}, to=sid)

@sio.on("SyncRequest")
async def handle_sync_request(sid, data):
    """
    Client manually requests missed events (e.g., after a reconnection).
    Data format: {"stateId": 15, "lastTimestamp": 1715856000.123}
    """
    state_id = data.get("stateId")
    last_timestamp = data.get("lastTimestamp")
    if state_id and last_timestamp:
        await SocketManager.sync_missed_events(sid, state_id, last_timestamp)

@sio.on("LocationUpdate")
async def handle_location_update(sid, data):
    """
    Handle live location updates from ambulances.
    Data: {"ambulanceId": 123, "latitude": 9.1, "longitude": 7.4, "stateId": 15}
    """
    ambulance_id = data.get("ambulanceId")
    state_id = data.get("stateId")
    
    # Broadcast to ambulance-specific room (e.g., for specific tracking)
    if ambulance_id:
        await sio.emit("AmbulanceLocation", data, room=f"ambulance-{ambulance_id}")
    
    # Broadcast to state group (e.g., for dispatchers on the dashboard)
    if state_id:
        await sio.emit("AmbulanceLocation", data, room=f"state-{state_id}")
