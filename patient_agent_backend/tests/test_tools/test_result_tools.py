import json

import pytest

from app.agent.request_context import set_patient_session
from app.tools.result_tools import create_result_tools


class FakeMedicalRecordService:
    async def query_patient_records(self, patient_id: int, start_date: str | None = None, end_date: str | None = None):
        assert patient_id == 7
        assert start_date == "2026-06-01"
        assert end_date == "2026-07-01"
        return type(
            "MedicalRecordListResponse",
            (),
            {
                "items": [
                    type(
                        "MedicalRecordItem",
                        (),
                        {"model_dump": lambda self: {"medicalRecordId": 101, "visitDate": "2026-07-01"}},
                    )()
                ]
            },
        )()


class FakePrescriptionService:
    async def query_patient_prescriptions(self, patient_id: int, start_date: str | None = None, end_date: str | None = None):
        return type("PrescriptionListResponse", (), {"items": []})()


class FakeHmsClient:
    def __init__(self):
        self.medical_record_service = FakeMedicalRecordService()
        self.prescription_service = FakePrescriptionService()


@pytest.mark.asyncio
async def test_query_my_medical_records_uses_logged_in_patient_context():
    set_patient_session(type("Session", (), {"patient_id": 7})())
    tools = create_result_tools(FakeHmsClient())
    query_my_medical_records = next(tool for tool in tools if tool.name == "query_my_medical_records")

    response = await query_my_medical_records.ainvoke(
        {"start_date": "2026-06-01", "end_date": "2026-07-01"}
    )
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["data"][0]["medicalRecordId"] == 101
