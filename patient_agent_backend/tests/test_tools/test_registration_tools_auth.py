import json

import pytest

from app.agent.request_context import set_patient_session
from app.tools.registration_tools import create_registration_tools


class FakeRegistrationService:
    async def create(self, request):
        return type("Resp", (), {"model_dump": lambda self: {"id": 1, "status": 0}})()


class FakeHmsClient:
    def __init__(self):
        self.registration_service = FakeRegistrationService()


@pytest.mark.asyncio
async def test_create_registration_requires_logged_in_patient():
    set_patient_session(None)
    tools = create_registration_tools(FakeHmsClient())
    create_registration = next(tool for tool in tools if tool.name == "create_registration")

    result = await create_registration.ainvoke(
        {
            "work_plan_id": 1,
            "doctor_schedule_id": 2,
            "doctor_id": 3,
            "dept_sub_id": 4,
            "appointment_date": "2026-06-25",
            "slot": 1,
        }
    )

    payload = json.loads(result)
    assert payload["ok"] is False
    assert "请先登录" in payload["error"]
