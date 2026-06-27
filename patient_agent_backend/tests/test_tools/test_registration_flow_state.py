import json

import pytest

from app.agent.request_context import set_patient_session, set_thread_id
from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store
from app.tools.registration_tools import create_registration_tools


class FakeRegistrationService:
    def __init__(self):
        self.create_requests = []

    async def create(self, request):
        self.create_requests.append(request)
        return type("Resp", (), {"model_dump": lambda self: {"id": 1, "status": 0}})()


class FakeHmsClient:
    def __init__(self):
        self.registration_service = FakeRegistrationService()


@pytest.mark.asyncio
async def test_create_registration_requires_pending_confirmation():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    set_patient_session(type("Session", (), {"patient_id": 9})())
    set_thread_id("thread-1")
    client = FakeHmsClient()
    tools = create_registration_tools(client)
    create_registration = next(tool for tool in tools if tool.name == "create_registration")

    result = await create_registration.ainvoke(
        {
            "work_plan_id": 1,
            "doctor_schedule_id": 2,
            "doctor_id": 3,
            "dept_sub_id": 4,
            "appointment_date": "2026-06-26",
            "slot": 1,
        }
    )

    payload = json.loads(result)
    assert payload["ok"] is False
    assert "请先确认挂号信息" in payload["error"]
    assert client.registration_service.create_requests == []


@pytest.mark.asyncio
async def test_create_registration_allows_confirmed_flow_state():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    await store.save(
        "patient:9:thread-1",
        {
            "pending_registration_confirmation": {
                "work_plan_id": 1,
                "doctor_schedule_id": 2,
                "doctor_id": 3,
                "dept_sub_id": 4,
                "appointment_date": "2026-06-26",
                "slot": 1,
            }
        },
    )
    set_patient_session(type("Session", (), {"patient_id": 9})())
    set_thread_id("thread-1")
    client = FakeHmsClient()
    tools = create_registration_tools(client)
    create_registration = next(tool for tool in tools if tool.name == "create_registration")

    result = await create_registration.ainvoke(
        {
            "work_plan_id": 1,
            "doctor_schedule_id": 2,
            "doctor_id": 3,
            "dept_sub_id": 4,
            "appointment_date": "2026-06-26",
            "slot": 1,
        }
    )

    payload = json.loads(result)
    assert payload["ok"] is True
    assert client.registration_service.create_requests[0].patient_id == 9


@pytest.mark.asyncio
async def test_create_registration_backfills_missing_args_from_pending_confirmation():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    await store.save(
        "patient:9:thread-2",
        {
            "pending_registration_confirmation": {
                "work_plan_id": 11,
                "doctor_schedule_id": 22,
                "doctor_id": 33,
                "dept_sub_id": 44,
                "appointment_date": "2026-06-28",
                "slot": 1,
                "schedule_options": [
                    {"doctor_schedule_id": 22, "slot": 1},
                    {"doctor_schedule_id": 23, "slot": 2},
                ],
            }
        },
    )
    set_patient_session(type("Session", (), {"patient_id": 9})())
    set_thread_id("thread-2")
    client = FakeHmsClient()
    tools = create_registration_tools(client)
    create_registration = next(tool for tool in tools if tool.name == "create_registration")

    result = await create_registration.ainvoke({"slot": 2})

    payload = json.loads(result)
    assert payload["ok"] is True
    request = client.registration_service.create_requests[0]
    assert request.patient_id == 9
    assert request.work_plan_id == 11
    assert request.doctor_schedule_id == 23
    assert request.doctor_id == 33
    assert request.dept_sub_id == 44
    assert str(request.appointment_date) == "2026-06-28"
    assert request.slot == 2
