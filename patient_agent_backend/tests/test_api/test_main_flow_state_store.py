from app.chat.flow_state import RedisFlowStateStore
from app.main import create_flow_state_store


class FakeRedisClient:
    pass


def test_create_flow_state_store_uses_redis_client_and_settings():
    store = create_flow_state_store(FakeRedisClient())

    assert isinstance(store, RedisFlowStateStore)
    assert store._redis.__class__ is FakeRedisClient
