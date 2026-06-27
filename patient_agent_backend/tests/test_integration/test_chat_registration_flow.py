from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api import chat as chat_module
from app.api.chat import router as chat_router, set_memory
from app.auth.dependencies import require_patient_session
from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store
from app.hms_client.models import ScheduleDetailResponse, ScheduleItem
from app.tools import ALL_TOOLS, init_tools


class FakeMemory:
    async def load_messages(self, patient_id, thread_id):
        return []

    async def save_messages(self, patient_id, thread_id, history):
        return None


class FakeDoctorService:
    async def schedule_detail(self, request):
        return ScheduleDetailResponse(
            work_plan_id=request.work_plan_id,
            doctor_id=3,
            doctor_name="张医生",
            dept_sub_id=4,
            date="2026-06-26",
            maximum=10,
            num=3,
            schedules=[
                ScheduleItem(
                    id=2,
                    work_plan_id=request.work_plan_id,
                    slot=1,
                    maximum=10,
                    num=3,
                )
            ],
        )


class FakeHmsClient:
    def __init__(self):
        self.doctor_service = FakeDoctorService()


class FakeGraph:
    async def ainvoke(self, state):
        query_schedule_detail = next(
            tool for tool in ALL_TOOLS if tool.name == "query_schedule_detail"
        )
        await query_schedule_detail.ainvoke({"work_plan_id": 11})
        return {
            "messages": [AIMessage(content="请确认挂号信息后，我再为您创建挂号。")],
            "needs_handoff": False,
        }


class FakeSession:
    token = "token-1"
    patient_id = 88
    name = "张三"
    phone = "13800138000"


def test_chat_registration_flow_sets_pending_confirmation_state():
    app = FastAPI()
    app.include_router(chat_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()

    set_memory(FakeMemory())
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    init_tools(FakeHmsClient())
    chat_module.compile_graph = lambda: FakeGraph()

    client = TestClient(app)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "帮我预约张医生今天的号", "thread_id": "flow-1"},
    )

    assert response.status_code == 200
    assert "请确认" in response.json()["message"]
    flow_state = store._data["patient:88:flow-1"]
    assert flow_state.pending_registration_confirmation == {
        "work_plan_id": 11,
        "doctor_schedule_id": 2,
        "doctor_id": 3,
        "dept_sub_id": 4,
        "appointment_date": "2026-06-26",
        "slot": 1,
        "doctor_name": "张医生",
        "schedule_options": [
            {
                "doctor_schedule_id": 2,
                "slot": 1,
            }
        ],
    }
