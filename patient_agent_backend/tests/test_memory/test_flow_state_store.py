import pytest

from app.chat.flow_state import FlowState, RedisFlowStateStore


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expiry = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value
        self.expiry[key] = ex

    async def delete(self, key):
        self.data.pop(key, None)
        self.expiry.pop(key, None)


@pytest.mark.asyncio
async def test_redis_flow_state_store_round_trip():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)

    await store.save(
        "patient:8:thread-1",
        {"pending_registration_confirmation": {"work_plan_id": 11}},
    )
    result = await store.load("patient:8:thread-1")

    assert isinstance(result, FlowState)
    assert result.pending_registration_confirmation == {"work_plan_id": 11}
    assert redis.expiry["chat:flow-state:8:thread-1"] == 60


@pytest.mark.asyncio
async def test_redis_flow_state_store_returns_empty_state_for_missing_key():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)

    result = await store.load("patient:8:missing")

    assert result == FlowState()


@pytest.mark.asyncio
async def test_redis_flow_state_store_restores_int_keys_for_schedule_candidates():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)

    await store.save(
        "patient:8:thread-2",
        {
            "schedule_candidates_by_work_plan": {
                11: {"doctor_id": 3, "appointment_date": "2026-06-28"}
            }
        },
    )

    result = await store.load("patient:8:thread-2")

    assert result.schedule_candidates_by_work_plan == {
        11: {"doctor_id": 3, "appointment_date": "2026-06-28"}
    }
