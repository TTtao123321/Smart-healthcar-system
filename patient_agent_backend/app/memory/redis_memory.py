"""Redis 对话记忆 — 生产级持久化"""

import json
import logging

import redis.asyncio as aioredis

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisMemory:
    """Redis 对话记忆管理"""

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or settings.redis_url
        self._redis: aioredis.Redis | None = None
        self._prefix = "chat:memory:"
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

        await self._redis.set(key, json.dumps(messages, ensure_ascii=False), ex=86400 * 7)

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
