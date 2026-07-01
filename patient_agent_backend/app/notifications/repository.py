import json
from typing import Any

from app.notifications.models import NotificationItem


class InMemoryNotificationRepository:
    def __init__(self):
        self._notifications: dict[int, list[NotificationItem]] = {}
        self._processed_events: set[str] = set()

    async def mark_processed(self, event_id: str) -> bool:
        if event_id in self._processed_events:
            return False
        self._processed_events.add(event_id)
        return True

    async def save(self, patient_id: int, item: NotificationItem) -> None:
        self._notifications.setdefault(patient_id, []).insert(0, item)

    async def list_recent(self, patient_id: int, limit: int = 5) -> list[NotificationItem]:
        return self._notifications.get(patient_id, [])[:limit]


class RedisNotificationRepository:
    def __init__(self, redis_client, *, prefix: str = "patient_notifications"):
        self._redis = redis_client
        self._prefix = prefix

    def _list_key(self, patient_id: int) -> str:
        return f"{self._prefix}:list:{patient_id}"

    def _event_key(self, event_id: str) -> str:
        return f"{self._prefix}:event:{event_id}"

    async def mark_processed(self, event_id: str) -> bool:
        return bool(await self._redis.set(self._event_key(event_id), "1", ex=60 * 60 * 24 * 7, nx=True))

    async def save(self, patient_id: int, item: NotificationItem) -> None:
        await self._redis.lpush(self._list_key(patient_id), item.model_dump_json())
        await self._redis.ltrim(self._list_key(patient_id), 0, 49)

    async def list_recent(self, patient_id: int, limit: int = 5) -> list[NotificationItem]:
        rows = await self._redis.lrange(self._list_key(patient_id), 0, max(limit - 1, 0))
        items: list[NotificationItem] = []
        for row in rows:
            if isinstance(row, bytes):
                row = row.decode("utf-8")
            payload: dict[str, Any] = json.loads(row)
            items.append(NotificationItem(**payload))
        return items
