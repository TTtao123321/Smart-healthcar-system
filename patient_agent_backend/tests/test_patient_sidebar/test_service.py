import pytest

from app.patient_profile.models import PatientProfile
from app.patient_sidebar.service import PatientSidebarService


class StubProfileService:
    async def get_by_id(self, patient_id: int):
        return PatientProfile(
            id=patient_id,
            uuid="u1",
            name="张三",
            sex="男",
            pid="110101199001011234",
            tel="13812341024",
            birthday="1990-01-01",
            insurance_type=None,
            medical_history=None,
            allergy_history=None,
            family_history=None,
        )


class StubRegistrationService:
    async def query_recent(self, patient_id: int, limit: int = 3):
        return [
            {"registrationId": 9, "date": "2026-06-18", "deptSubName": "呼吸内科", "doctorName": "李芳"},
        ]


class StubScheduleGateway:
    async def get_today_schedule(self):
        return {
            "dateLabel": "2026年6月24日 周三",
            "departments": [
                {
                    "departmentId": "1",
                    "departmentName": "内科",
                    "doctors": [
                        {
                            "doctorId": "2",
                            "doctorName": "张明华",
                            "title": "主任医师",
                            "bio": "擅长心血管疾病诊疗",
                            "timeSlots": ["08:00-12:00"],
                        }
                    ],
                }
            ],
        }


@pytest.mark.asyncio
async def test_get_sidebar_aggregates_profile_visits_and_schedule():
    service = PatientSidebarService(
        profile_service=StubProfileService(),
        registration_service=StubRegistrationService(),
        schedule_gateway=StubScheduleGateway(),
    )

    result = await service.get_sidebar(123)

    assert result.profile.patientId == "123"
    assert result.recentVisits[0].doctorName == "李芳"
    assert result.schedule.departments[0].departmentName == "内科"
