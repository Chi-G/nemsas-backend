import json
import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any, Optional
from uuid import UUID
import redis.asyncio as redis
from app.core.config import settings
from app.models.device import Device
from app.crud.device import device_crud
from sqlalchemy.ext.asyncio import AsyncSession
import time

import os
from pathlib import Path

# Initialize Firebase if service account path is provided
if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
    path_str = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    if path_str.startswith("/"):
        path_str = path_str[1:]  # strip leading slash to resolve relatively
        
    project_root = Path(__file__).resolve().parent.parent.parent
    full_path = project_root / path_str
    cwd_path = Path.cwd() / path_str
    
    resolved_path = None
    if os.path.exists(full_path):
        resolved_path = full_path
    elif os.path.exists(cwd_path):
        resolved_path = cwd_path
    elif os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
        resolved_path = Path(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        
    if resolved_path:
        try:
            cred = credentials.Certificate(str(resolved_path))
            firebase_admin.initialize_app(cred)
            print(f"[Notification] Firebase successfully initialized with: {resolved_path}")
        except Exception as e:
            print(f"[Notification] Error initializing Firebase: {e}")
    else:
        print(f"[Notification] Warning: Firebase service account credentials file not found at {full_path} or {cwd_path}")

class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def _push_to_fcm(self, tokens: List[str], title: str, body: str, data: Dict[str, str] = None):
        if not tokens:
            return
        
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )
        try:
            response = messaging.send_multicast(message)
            print(f"[Notification] Successfully sent {response.success_count} messages")
            if response.failure_count > 0:
                print(f"[Notification] Failed to send {response.failure_count} messages")
        except Exception as e:
            print(f"[Notification] FCM error: {e}")

    async def _cache_notification(self, user_id: str, notification_id: str, payload: Dict[str, Any]):
        key = f"notifications:{user_id}"
        # Store in a hash or list. Using a list for historical order.
        await self.redis_client.lpush(key, json.dumps(payload))
        # Keep only last 100
        await self.redis_client.ltrim(key, 0, 99)
        # Set expiration to 30 days
        await self.redis_client.expire(key, 60*60*24*30)

    async def send_to_user(self, db: AsyncSession, user_id: UUID, title: str, body: str, data: Dict[str, Any] = None):
        # 1. Get all devices
        devices = await device_crud.get_multi_by_user(db, user_id=user_id)
        tokens = [d.push_token for d in devices]
        
        notification_id = f"notif_{int(time.time() * 1000)}"
        payload = {
            "id": notification_id,
            "title": title,
            "body": body,
            "data": data,
            "timestamp": time.time(),
            "read": False
        }

        # 2. Cache in Redis
        await self._cache_notification(str(user_id), notification_id, payload)
        
        # 3. Push to devices
        # FCM data must be strings
        fcm_data = {k: str(v) for k, v in (data or {}).items()}
        fcm_data["notificationId"] = notification_id
        
        await self._push_to_fcm(tokens, title, body, fcm_data)

    async def send_to_ambulance(self, db: AsyncSession, ambulance_id: int, title: str, body: str, data: Dict[str, Any] = None):
        # Find all devices linked to this ambulance
        devices = await device_crud.get_multi_by_ambulance(db, ambulance_id=ambulance_id)
        
        # We also want to find users directly linked to this ambulance in the User model
        # For now, let's trust the Device model's ambulance_id which should be set on login/registration
        
        user_ids = list(set([str(d.user_id) for d in devices]))
        
        notification_id = f"notif_{int(time.time() * 1000)}"
        payload = {
            "id": notification_id,
            "title": title,
            "body": body,
            "data": data,
            "timestamp": time.time(),
            "read": False
        }

        # Cache for each user
        for uid in user_ids:
            await self._cache_notification(uid, notification_id, payload)
            
        # Push to all tokens
        tokens = [d.push_token for d in devices]
        fcm_data = {k: str(v) for k, v in (data or {}).items()}
        fcm_data["notificationId"] = notification_id
        
        await self._push_to_fcm(tokens, title, body, fcm_data)

    async def get_pending_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        key = f"notifications:{user_id}"
        items = await self.redis_client.lrange(key, 0, -1)
        return [json.loads(i) for i in items]

    async def mark_as_read(self, user_id: str, notification_id: str):
        key = f"notifications:{user_id}"
        items = await self.redis_client.lrange(key, 0, -1)
        
        for i, item_str in enumerate(items):
            item = json.loads(item_str)
            if item["id"] == notification_id:
                item["read"] = True
                await self.redis_client.lset(key, i, json.dumps(item))
                break

notification_service = NotificationService()
