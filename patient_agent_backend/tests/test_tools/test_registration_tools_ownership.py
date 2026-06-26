import json

import pytest

from app.agent.request_context import set_patient_session
from app.hms_client.models import RegistrationItem, RegistrationQueryResponse
from app.tools.registration_tools import create_registration_tools


class FakeRegistrationService:
    def __init__(self, items=None):
        self.items = items or []
        self.query_requests = []
        self.cancel_requests = []

    async def query(self, request):
        self.query_requests.append(request)
        return RegistrationQueryResponse(items=self.items)

    async def cancel(self, request):
        self.cancel_requests.append(request)
        return type("Resp", (), {"model_dump": lambda self: {"result": 1}})()


class FakeHmsClient:
    def __init__(self, items=None):
        self.registration_service = FakeRegistrationService(items=items)


@pytest.mark.asyncio
async def test_query_registration_uses_session_patient_id():
    set_patient_session(type("Session", (), {"patient_id": 88})())
    client = FakeHmsClient(items=[RegistrationItem(id=9, patient_id=88)])
    tools = create_registration_tools(client)
    query_registration = next(tool for tool in tools if tool.name == "query_registration")

    result = await query_registration.ainvoke({"registration_id": 9})

    payload = json.loads(result)
    assert payload["ok"] is True
    assert client.registration_service.query_requests[0].patient_id == 88


@pytest.mark.asyncio
async def test_cancel_registration_rejects_unowned_record():
    set_patient_session(type("Session", (), {"patient_id": 88})())
    client = FakeHmsClient(items=[])
    tools = create_registration_tools(client)
    cancel_registration = next(tool for tool in tools if tool.name == "cancel_registration")

    result = await cancel_registration.ainvoke({"registration_id": 9})

    payload = json.loads(result)
    assert payload["ok"] is False
    assert "无权限" in payload["error"]
    assert client.registration_service.cancel_requests == []
