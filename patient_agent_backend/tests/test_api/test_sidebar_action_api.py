from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from app.api import chat as chat_module
from app.api.chat import set_memory
from app.api.patient import router as patient_router
from app.auth.dependencies import require_patient_session


class FakeMemory:
    async def load_messages(self, patient_id, thread_id):
        return []

    async def save_messages(self, patient_id, thread_id, history):
        return None


class FakeGraph:
    def __init__(self):
        self.state = None

    async def ainvoke(self, state):
        self.state = state
        return {
            "messages": [AIMessage(content="已收到侧栏确认，将继续挂号流程。")],
            "needs_handoff": False,
        }


class FakeSession:
    token = "token-1"
    patient_id = 88
    name = "张三"
    phone = "13800138000"


def test_sidebar_action_uses_authenticated_patient():
    app = FastAPI()
    app.include_router(patient_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()

    graph = FakeGraph()
    set_memory(FakeMemory())
    chat_module.compile_graph = lambda: graph

    client = TestClient(app)
    response = client.post(
        "/api/patient/sidebar/action",
        headers={"Authorization": "Bearer token-1"},
        json={
            "action": "confirm_registration",
            "thread_id": "thread-9",
            "payload": {"doctor_id": 12, "department_name": "内科"},
        },
    )

    assert response.status_code == 200
    assert response.json()["thread_id"] == "thread-9"
    assert graph.state["patient_id"] == 88
    assert isinstance(graph.state["messages"][-1], HumanMessage)
    assert "confirm_registration" in graph.state["messages"][-1].content
