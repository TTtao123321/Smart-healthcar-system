from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api.chat import set_memory
from app.api.clinician_chat import router as clinician_chat_router


class FakeMemory:
    async def load_messages(self, patient_id, thread_id):
        return []

    async def save_messages(self, patient_id, thread_id, history):
        self.saved = (patient_id, thread_id, history)


class FakeGraph:
    def __init__(self, captured):
        self._captured = captured

    async def ainvoke(self, state):
        self._captured["state"] = state
        return {"messages": [AIMessage(content="临床回复")], "needs_handoff": False}


def test_clinician_chat_uses_clinician_channel_context(monkeypatch):
    app = FastAPI()
    app.include_router(clinician_chat_router)
    set_memory(FakeMemory())
    captured = {}

    def graph_factory(**kwargs):
        captured.update(kwargs)
        return FakeGraph(captured)

    monkeypatch.setattr("app.api.clinician_chat.compile_graph", graph_factory)

    client = TestClient(app)
    response = client.post(
        "/api/clinician/chat",
        json={
            "message": "查一下患者7的历史病历",
            "threadId": "clinician-thread-1",
            "userId": 9,
            "roleCodes": ["DOCTOR"],
            "deptScope": [3],
            "doctorScope": [12],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["channel"] == "clinician"
    assert body["thread_id"] == "clinician-thread-1"
    assert body["message"] == "临床回复"
    assert captured["channel"] == "clinician"
    assert captured["clinician_context"].user_id == 9
    assert captured["clinician_context"].role_codes == ["DOCTOR"]
    assert captured["clinician_context"].dept_scope == [3]
    assert captured["clinician_context"].doctor_scope == [12]
    assert captured["state"]["patient_id"] == 9
