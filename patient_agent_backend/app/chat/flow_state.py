from dataclasses import dataclass, field


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


class InMemoryFlowStateStore:
    def __init__(self):
        self._data: dict[str, FlowState] = {}

    async def load(self, thread_key: str) -> FlowState:
        return self._data.get(thread_key, FlowState())

    async def save(self, thread_key: str, payload: dict | FlowState) -> None:
        if isinstance(payload, FlowState):
            self._data[thread_key] = payload
            return
        self._data[thread_key] = FlowState(**payload)

    async def delete(self, thread_key: str) -> None:
        self._data.pop(thread_key, None)


_flow_state_store: InMemoryFlowStateStore | None = None


def set_flow_state_store(store: InMemoryFlowStateStore | None) -> None:
    global _flow_state_store
    _flow_state_store = store


def get_flow_state_store() -> InMemoryFlowStateStore:
    global _flow_state_store
    if _flow_state_store is None:
        _flow_state_store = InMemoryFlowStateStore()
    return _flow_state_store
