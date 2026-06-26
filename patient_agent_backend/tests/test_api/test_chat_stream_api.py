from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import router as chat_router
from app.auth.dependencies import require_patient_session


class FakeSession:
    token = "token-1"
    patient_id = 88
    name = "张三"
    phone = "13800138000"


class FakeStreamOrchestrator:
    async def run_stream(self, *, session, user_message: str, thread_id: str):
        yield {
            "event": "message",
            "data": {"content": "系统暂时无法处理该请求，请稍后再试。", "thread_id": thread_id},
        }
        yield {
            "event": "done",
            "data": {"thread_id": thread_id},
        }


def create_client(monkeypatch):
    from app.api import chat as chat_module

    app = FastAPI()
    app.include_router(chat_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()
    monkeypatch.setattr(chat_module, "get_orchestrator", lambda: FakeStreamOrchestrator(), raising=False)
    return TestClient(app)


def test_chat_stream_returns_orchestrator_events(monkeypatch):
    client = create_client(monkeypatch)

    response = client.post(
        "/api/chat/stream",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "我要挂号", "thread_id": "t-1"},
    )

    assert response.status_code == 200
    assert "event: message" in response.text
    assert "系统暂时无法处理该请求，请稍后再试。" in response.text
    assert "event: done" in response.text
