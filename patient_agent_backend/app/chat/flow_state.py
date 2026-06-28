import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class FlowState:
    intent: str | None = None
    selected_dept: dict | None = None
    selected_doctor: dict | None = None
    selected_date: str | None = None
    selected_work_plan_id: int | None = None
    selected_schedule_slot: dict | None = None
    pending_registration_confirmation: dict | None = None
    schedule_candidates_by_work_plan: dict[int, dict] | None = None


def _build_flow_state(thread_key: str, payload: dict | FlowState | None = None) -> FlowState:
    if payload is None:
        return FlowState()
    if isinstance(payload, FlowState):
        return payload

    normalized = dict(payload)
    candidates = normalized.get("schedule_candidates_by_work_plan")
    if isinstance(candidates, dict):
        normalized["schedule_candidates_by_work_plan"] = {
            int(key): value for key, value in candidates.items()
        }
    return FlowState(**normalized)


class FlowStateStore(ABC):
    @abstractmethod
    async def load(self, thread_key: str) -> FlowState:
        """Load thread-scoped flow state."""

    @abstractmethod
    async def save(self, thread_key: str, payload: dict | FlowState) -> None:
        """Persist thread-scoped flow state."""

    @abstractmethod
    async def delete(self, thread_key: str) -> None:
        """Delete thread-scoped flow state."""


class InMemoryFlowStateStore(FlowStateStore):
    def __init__(self):
        self._data: dict[str, FlowState] = {}

    async def load(self, thread_key: str) -> FlowState:
        return self._data.get(thread_key, FlowState())

    async def save(self, thread_key: str, payload: dict | FlowState) -> None:
        self._data[thread_key] = _build_flow_state(thread_key, payload)

    async def delete(self, thread_key: str) -> None:
        self._data.pop(thread_key, None)


class RedisFlowStateStore(FlowStateStore):
    def __init__(self, redis_client, ttl_seconds: int = 60 * 60 * 24):
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _redis_key(thread_key: str) -> str:
        parts = thread_key.split(":", 2)
        if len(parts) != 3 or parts[0] != "patient":
            raise ValueError(f"invalid flow state thread key: {thread_key}")
        _, patient_id, thread_id = parts
        return f"chat:flow-state:{patient_id}:{thread_id}"

    async def load(self, thread_key: str) -> FlowState:
        raw = await self._redis.get(self._redis_key(thread_key))
        if not raw:
            return FlowState()
        return _build_flow_state(thread_key, json.loads(raw))

    async def save(self, thread_key: str, payload: dict | FlowState) -> None:
        state = _build_flow_state(thread_key, payload)
        await self._redis.set(
            self._redis_key(thread_key),
            json.dumps(asdict(state), ensure_ascii=False),
            ex=self._ttl_seconds,
        )

    async def delete(self, thread_key: str) -> None:
        await self._redis.delete(self._redis_key(thread_key))


_flow_state_store: FlowStateStore | None = None


def set_flow_state_store(store: FlowStateStore | None) -> None:
    global _flow_state_store
    _flow_state_store = store


def get_flow_state_store() -> FlowStateStore:
    global _flow_state_store
    if _flow_state_store is None:
        _flow_state_store = InMemoryFlowStateStore()
    return _flow_state_store
