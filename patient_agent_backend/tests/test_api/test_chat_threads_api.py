from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import router as chat_router, set_memory
from app.auth.dependencies import require_patient_session


class FakeSession:
    token = "token-1"
    patient_id = 1
    name = "张三"
    phone = "13800138001"


class FakeMemory:
    def __init__(self):
        self.deleted = []

    async def list_threads(self, patient_id, limit=None):
        assert patient_id == 1
        return [
            {
                "thread_id": "thread-1",
                "title": "我想挂号心内科",
                "last_message": "已为您找到今日可预约医生。",
                "updated_at": "2026-06-27T14:00:00",
                "message_count": 2,
            }
        ]

    async def delete_thread(self, patient_id, thread_id):
        self.deleted.append((patient_id, thread_id))


def create_client(memory, with_auth_override=True):
    app = FastAPI()
    app.include_router(chat_router)
    set_memory(memory)
    if with_auth_override:
        app.dependency_overrides[require_patient_session] = lambda: FakeSession()
    return TestClient(app)


def test_chat_threads_returns_authenticated_patient_threads():
    client = create_client(FakeMemory())

    response = client.get("/api/chat/threads", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["threads"][0]["thread_id"] == "thread-1"


def test_delete_thread_uses_authenticated_patient_id():
    memory = FakeMemory()
    client = create_client(memory)

    response = client.delete("/api/chat/threads/thread-1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert memory.deleted == [(1, "thread-1")]


def test_chat_threads_requires_login():
    client = create_client(FakeMemory(), with_auth_override=False)

    response = client.get("/api/chat/threads")

    assert response.status_code == 401
