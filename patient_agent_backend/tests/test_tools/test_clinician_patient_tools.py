import json

import pytest

from app.clinician.context import set_clinician_context
from app.clinician.models import ClinicianContext
from app.hms_client.models import MedicalRecordListItem, MedicalRecordListResponse, RegistrationItem
from app.tools.clinician_patient_tools import create_clinician_patient_tools


class FakeRegistrationService:
    async def query(self, request):
        return type(
            "RegistrationQueryResponse",
            (),
            {
                "items": [
                    RegistrationItem(
                        id=11,
                        patient_id=request.patient_id,
                        doctor_id=12,
                        dept_sub_id=3,
                    ),
                    RegistrationItem(
                        id=12,
                        patient_id=request.patient_id,
                        doctor_id=99,
                        dept_sub_id=8,
                    ),
                ]
            },
        )()


class FakeMedicalRecordService:
    async def query_patient_records(self, patient_id: int, start_date=None, end_date=None):
        return MedicalRecordListResponse(
            items=[
                MedicalRecordListItem(
                    medicalRecordId=101,
                    registrationId=11,
                    visitDate="2026-06-14",
                    department="口腔科",
                    doctorName="王文彦",
                    chiefComplaintSummary="左眼视物模糊1周",
                    status="PRESCRIPTION_READY",
                ),
                MedicalRecordListItem(
                    medicalRecordId=102,
                    registrationId=12,
                    visitDate="2026-06-20",
                    department="皮肤科",
                    doctorName="未授权医生",
                    chiefComplaintSummary="皮疹",
                    status="RECORD_READY",
                ),
            ]
        )


class FakeHmsClient:
    def __init__(self):
        self.requests = []
        self.registration_service = FakeRegistrationService()
        self.medical_record_service = FakeMedicalRecordService()

    async def post(self, path: str, json: dict | None = None):
        self.requests.append({"path": path, "json": json})
        return {
            "result": {
                "list": [
                    {
                        "patientId": 7,
                        "name": "张三",
                        "sex": "男",
                        "tel": "13800138007",
                    },
                    {
                        "patientId": 8,
                        "name": "张三丰",
                        "sex": "男",
                        "tel": "13800138008",
                    },
                ],
                "totalCount": 2,
            }
        }


@pytest.mark.asyncio
async def test_search_patient_profiles_posts_name_and_filters_phone_suffix():
    set_clinician_context(ClinicianContext(user_id=9, role_codes=["DOCTOR"]))
    hms_client = FakeHmsClient()
    tools = create_clinician_patient_tools(hms_client)
    search_patient_profiles = next(
        tool for tool in tools if tool.name == "search_patient_profiles"
    )

    response = await search_patient_profiles.ainvoke(
        {"name": "张三", "phone_suffix": "8007"}
    )
    payload = json.loads(response)

    assert hms_client.requests == [
        {
            "path": "/patient/selectByPage",
            "json": {"page": 1, "length": 10, "name": "张三"},
        }
    ]
    assert payload["ok"] is True
    assert [item["patientId"] for item in payload["data"]] == [7]
    assert payload["data"][0]["phoneMasked"] == "138****8007"


@pytest.mark.asyncio
async def test_query_patient_medical_records_filters_by_clinician_scope():
    set_clinician_context(
        ClinicianContext(
            user_id=9,
            role_codes=["DOCTOR"],
            dept_scope=[3],
            doctor_scope=[12],
        )
    )
    tools = create_clinician_patient_tools(FakeHmsClient())
    query_patient_medical_records = next(
        tool for tool in tools if tool.name == "query_patient_medical_records"
    )

    response = await query_patient_medical_records.ainvoke({"patient_id": 7, "limit": 3})
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["summary"] == "已查询到患者历史病历"
    assert [item["medicalRecordId"] for item in payload["data"]] == [101]
    assert payload["data"][0]["doctorName"] == "王文彦"


@pytest.mark.asyncio
async def test_query_patient_medical_records_requires_clinician_context():
    set_clinician_context(None)
    tools = create_clinician_patient_tools(FakeHmsClient())
    query_patient_medical_records = next(
        tool for tool in tools if tool.name == "query_patient_medical_records"
    )

    response = await query_patient_medical_records.ainvoke({"patient_id": 7})
    payload = json.loads(response)

    assert payload["ok"] is False
    assert "临床身份上下文缺失" in payload["error"]
