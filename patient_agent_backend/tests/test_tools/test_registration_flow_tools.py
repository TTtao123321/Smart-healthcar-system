import json

import pytest

from app.agent.request_context import set_patient_session, set_thread_id
from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store
from app.hms_client.models import ScheduleDetailResponse, ScheduleItem
from app.tools.doctor_tools import create_doctor_tools


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


@pytest.mark.asyncio
async def test_query_schedule_detail_sets_pending_confirmation_flow_state():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    set_patient_session(type("Session", (), {"patient_id": 88})())
    set_thread_id("thread-1")
    tools = create_doctor_tools(FakeHmsClient())
    query_schedule_detail = next(tool for tool in tools if tool.name == "query_schedule_detail")

    result = await query_schedule_detail.ainvoke({"work_plan_id": 11})

    payload = json.loads(result)
    assert payload["ok"] is True
    assert store._data["patient:88:thread-1"].pending_registration_confirmation == {
        "work_plan_id": 11,
        "doctor_schedule_id": 2,
        "doctor_id": 3,
        "dept_sub_id": 4,
        "appointment_date": "2026-06-26",
        "slot": 1,
        "doctor_name": "张医生",
    }
