import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api import chat as chat_module
from app.api.chat import router as chat_router, set_memory
from app.auth.dependencies import require_patient_session
from app.middleware.request_context import RequestContextMiddleware


class FakeMemory:
    async def load_messages(self, patient_id, thread_id):
        return []

    async def save_messages(self, patient_id, thread_id, history):
        return None


class FakeGraph:
    async def ainvoke(self, state):
        return {
            "messages": [AIMessage(content="已查询到您的挂号记录。")],
            "needs_handoff": False,
            "guardrail_result": "health_topic",
        }


class FakeSession:
    token = "token-1"
    patient_id = 88
    name = "张三"
    phone = "13800138000"


def test_request_context_logs_request_and_patient(caplog):
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.include_router(chat_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()

    set_memory(FakeMemory())
    chat_module.compile_graph = lambda: FakeGraph()
    client = TestClient(app)

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/chat",
            headers={"Authorization": "Bearer token-1", "X-Request-ID": "req-123"},
            json={"message": "查看我的挂号", "thread_id": "log-1"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"
    assert any(getattr(record, "request_id", None) == "req-123" for record in caplog.records)
    assert any(getattr(record, "patient_id", None) == 88 for record in caplog.records)
