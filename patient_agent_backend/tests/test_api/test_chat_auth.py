from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api import chat as chat_module
from app.api.chat import router as chat_router, set_memory
from app.auth.dependencies import require_patient_session


class FakeMemory:
    def __init__(self):
        self.loaded = []
        self.saved = []

    async def load_messages(self, patient_id, thread_id):
        self.loaded.append((patient_id, thread_id))
        return []

    async def save_messages(self, patient_id, thread_id, history):
        self.saved.append((patient_id, thread_id, history))


class FakeGraph:
    def __init__(self):
        self.state = None

    async def ainvoke(self, state):
        self.state = state
        return {
            "messages": [AIMessage(content="ok")],
            "needs_handoff": False,
        }


class FakeSession:
    token = "token-1"
    patient_id = 88
    name = "张三"
    phone = "13800138000"


def create_client(fake_memory, fake_graph, with_auth_override):
    app = FastAPI()
    app.include_router(chat_router)
    set_memory(fake_memory)
    chat_module.compile_graph = lambda: fake_graph
    if with_auth_override:
        app.dependency_overrides[require_patient_session] = lambda: FakeSession()
    return TestClient(app)


def test_chat_requires_login():
    memory = FakeMemory()
    graph = FakeGraph()
    client = create_client(memory, graph, with_auth_override=False)

    response = client.post("/api/chat", json={"message": "我要挂号"})

    assert response.status_code == 401


def test_chat_ignores_forwarded_patient_id():
    memory = FakeMemory()
    graph = FakeGraph()
    client = create_client(memory, graph, with_auth_override=True)

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "你好", "patient_id": 999, "thread_id": "t-1"},
    )

    assert response.status_code == 200
    assert graph.state["patient_id"] == 88
    assert memory.loaded[0][0] == 88


def test_chat_history_uses_authenticated_patient_id():
    memory = FakeMemory()
    graph = FakeGraph()
    client = create_client(memory, graph, with_auth_override=True)

    response = client.get(
        "/api/chat/history",
        headers={"Authorization": "Bearer token-1"},
        params={"patient_id": 999, "thread_id": "t-2"},
    )

    assert response.status_code == 200
    assert memory.loaded[0][0] == 88
