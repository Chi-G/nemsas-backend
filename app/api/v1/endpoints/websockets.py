import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.notification_service import notification_service
from app.core.security import verify_token
from app.crud.user import user_crud

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_user_ws(token: str, db: AsyncSession):
    """Dependency to get the current user for websocket connection via token query param."""
    try:
        payload = verify_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await user_crud.get(db, id=int(user_id))
        return user
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        return None

@router.websocket("/incidents")
async def websocket_incidents(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    WebSocket endpoint for real-time incident notifications.
    Clients must connect with a valid JWT token in the query string:
    ws://domain/api/v1/ws/incidents?token=<jwt_token>
    """
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=1008, reason="Invalid authentication credentials")
        return

    await notification_service.connect(websocket, user)
    try:
        while True:
            # Keep connection alive, listen for ping/pong or client messages if needed
            data = await websocket.receive_text()
            # We don't process incoming messages from clients currently
    except WebSocketDisconnect:
        notification_service.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        notification_service.disconnect(websocket)
