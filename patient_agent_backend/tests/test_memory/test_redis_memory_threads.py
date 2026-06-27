import pytest

from app.memory.redis_memory import RedisMemory


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.hashes = {}
        self.sorted_sets = {}
        self.expires = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.expires[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def hset(self, key, mapping):
        self.hashes[key] = dict(mapping)

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def zadd(self, key, mapping):
        self.sorted_sets.setdefault(key, {})
        self.sorted_sets[key].update(mapping)

    async def zrevrange(self, key, start, end):
        items = self.sorted_sets.get(key, {})
        ordered = sorted(items.items(), key=lambda item: item[1], reverse=True)
        names = [name for name, _ in ordered]
        return names[start : end + 1 if end != -1 else None]

    async def expire(self, key, ttl):
        self.expires[key] = ttl

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.hashes.pop(key, None)
            self.sorted_sets.pop(key, None)
            self.expires.pop(key, None)

    async def zrem(self, key, member):
        if key in self.sorted_sets:
            self.sorted_sets[key].pop(member, None)


@pytest.mark.asyncio
async def test_save_thread_snapshot_updates_thread_index_and_meta():
    memory = RedisMemory("redis://unused")
    memory._redis = FakeRedis()

    messages = [
        {"role": "user", "content": "我想挂号心内科"},
        {"role": "assistant", "content": "已为您找到今日可预约医生。"},
    ]

    await memory.save_messages("1", "thread-1", messages)
    await memory.save_thread_snapshot("1", "thread-1", messages)

    threads = await memory.list_threads("1")

    assert threads == [
        {
            "thread_id": "thread-1",
            "title": "我想挂号心内科",
            "last_message": "已为您找到今日可预约医生。",
            "updated_at": threads[0]["updated_at"],
            "message_count": 2,
        }
    ]


@pytest.mark.asyncio
async def test_delete_thread_removes_body_meta_and_index():
    memory = RedisMemory("redis://unused")
    memory._redis = FakeRedis()
    messages = [{"role": "user", "content": "查询挂号记录"}]

    await memory.save_messages("1", "thread-1", messages)
    await memory.save_thread_snapshot("1", "thread-1", messages)
    await memory.delete_thread("1", "thread-1")

    assert await memory.load_messages("1", "thread-1") == []
    assert await memory.list_threads("1") == []
