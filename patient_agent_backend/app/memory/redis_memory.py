"""Redis 对话记忆 — 生产级持久化"""

import json
import logging
from datetime import datetime

import redis.asyncio as aioredis

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisMemory:
    """Redis 对话记忆管理"""

    _ttl_seconds = 86400 * 7

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or settings.redis_url
        self._redis: aioredis.Redis | None = None
        self._prefix = "chat:memory:"
        self._threads_prefix = "chat:threads:"
        self._thread_meta_prefix = "chat:threadmeta:"
        self._max_turns = settings.max_conversation_turns

    async def connect(self) -> None:
        """连接 Redis"""
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()

    def _key(self, patient_id: str, thread_id: str) -> str:
        """生成 Redis key"""
        return f"{self._prefix}{patient_id}:{thread_id}"

    def _threads_key(self, patient_id: str) -> str:
        return f"{self._threads_prefix}{patient_id}"

    def _thread_meta_key(self, patient_id: str, thread_id: str) -> str:
        return f"{self._thread_meta_prefix}{patient_id}:{thread_id}"

    @staticmethod
    def _build_thread_title(messages: list[dict]) -> str:
        first_user = next(
            (
                str(item["content"])
                for item in messages
                if item.get("role") == "user" and item.get("content")
            ),
            "",
        )
        if not first_user:
            return "新对话"
        return first_user[:12] + ("..." if len(first_user) > 12 else "")

    @staticmethod
    def _build_last_message(messages: list[dict]) -> str:
        for item in reversed(messages):
            content = item.get("content")
            if content:
                return str(content)[:30]
        return ""

    async def save_messages(
        self, patient_id: str, thread_id: str, messages: list[dict]
    ) -> None:
        """保存对话消息"""
        if not self._redis:
            return

        key = self._key(patient_id, thread_id)

        # 限制对话轮次
        if len(messages) > self._max_turns * 2:
            messages = messages[-(self._max_turns * 2):]

        await self._redis.set(
            key,
            json.dumps(messages, ensure_ascii=False),
            ex=self._ttl_seconds,
        )

    async def save_thread_snapshot(
        self, patient_id: str, thread_id: str, messages: list[dict]
    ) -> None:
        """保存线程摘要和索引"""
        if not self._redis:
            return

        updated_at = datetime.now().isoformat()
        updated_score = int(datetime.now().timestamp())
        meta_key = self._thread_meta_key(patient_id, thread_id)
        threads_key = self._threads_key(patient_id)
        mapping = {
            "thread_id": str(thread_id),
            "title": self._build_thread_title(messages),
            "last_message": self._build_last_message(messages),
            "updated_at": updated_at,
            "message_count": str(len(messages)),
        }

        await self._redis.hset(meta_key, mapping=mapping)
        await self._redis.zadd(threads_key, {str(thread_id): updated_score})
        await self._redis.expire(meta_key, self._ttl_seconds)
        await self._redis.expire(threads_key, self._ttl_seconds)

    async def list_threads(
        self, patient_id: str, limit: int | None = None
    ) -> list[dict]:
        """列出患者的历史会话线程"""
        if not self._redis:
            return []

        end = -1 if limit is None else max(limit - 1, 0)
        thread_ids = await self._redis.zrevrange(
            self._threads_key(patient_id), 0, end
        )
        threads = []

        for thread_id in thread_ids:
            meta = await self._redis.hgetall(
                self._thread_meta_key(patient_id, str(thread_id))
            )
            if not meta:
                continue
            threads.append(
                {
                    "thread_id": meta.get("thread_id", str(thread_id)),
                    "title": meta.get("title", "新对话"),
                    "last_message": meta.get("last_message", ""),
                    "updated_at": meta.get("updated_at", ""),
                    "message_count": int(meta.get("message_count", 0)),
                }
            )
        return threads

    async def load_messages(self, patient_id: str, thread_id: str) -> list[dict]:
        """加载对话消息"""
        if not self._redis:
            return []

        key = self._key(patient_id, thread_id)
        data = await self._redis.get(key)

        if not data:
            return []

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.error(f"对话记忆解析失败: {key}")
            return []

    async def clear_messages(self, patient_id: str, thread_id: str) -> None:
        """清除对话消息"""
        if not self._redis:
            return

        key = self._key(patient_id, thread_id)
        await self._redis.delete(key)

    async def delete_thread(self, patient_id: str, thread_id: str) -> None:
        """删除线程正文、摘要和索引"""
        if not self._redis:
            return

        await self._redis.delete(
            self._key(patient_id, thread_id),
            self._thread_meta_key(patient_id, thread_id),
        )
        await self._redis.zrem(self._threads_key(patient_id), str(thread_id))
