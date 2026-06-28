from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.auth.dependencies import require_patient_session
from app.api import auth as auth_module


class FakeSession:
    token = "e2e-token-1"
    patient_id = 12
    name = "张三"
    phone = "13800138000"


def create_client(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "patient_agent_e2e_mode", True, raising=False)
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()
    auth_module.set_redis(type("FakeRedis", (), {"set": lambda *args, **kwargs: None})())
    return TestClient(app)


def test_e2e_reset_returns_selected_scenario(monkeypatch):
    from app.api.e2e import router as e2e_router

    client = create_client(monkeypatch)
    client.app.include_router(e2e_router)

    response = client.post("/api/e2e/reset", json={"scenario": "delete_thread_failure"})

    assert response.status_code == 200
    assert response.json()["scenario"] == "delete_thread_failure"
    assert response.json()["delete_thread_should_fail"] is True


def test_send_sms_returns_fixed_e2e_code(monkeypatch):
    client = create_client(monkeypatch)

    response = client.post("/api/auth/send-sms", json={"phone": "13800138000"})

    assert response.status_code == 200
    assert response.json()["code_dev"] == "123456"


def test_chat_threads_returns_e2e_thread_list(monkeypatch):
    client = create_client(monkeypatch)

    response = client.get("/api/chat/threads", headers={"Authorization": "Bearer e2e-token-1"})

    assert response.status_code == 200
    assert response.json()["threads"][0]["thread_id"] == "thread-1"
