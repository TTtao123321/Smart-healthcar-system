from app.hms_client.models import RegistrationQueryRequest
from app.hms_client.services.registration_service import RegistrationService


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.requests = []

    async def post(self, path: str, json: dict | None = None):
        self.requests.append({"path": path, "json": json})
        return self.response


async def test_query_uses_patient_detail_endpoint_and_maps_registrations():
    client = FakeClient(
        {
            "result": {
                "registrations": [
                    {
                        "registrationId": 9,
                        "date": "2026-06-26",
                        "slot": 1,
                        "status": 0,
                        "paymentStatus": 1,
                        "doctorId": 3,
                        "deptSubId": 4,
                    }
                ]
            }
        }
    )
    service = RegistrationService(client)

    result = await service.query(RegistrationQueryRequest(patient_id=88))

    assert client.requests == [{"path": "/patient/selectDetail", "json": {"patientId": 88}}]
    assert len(result.items) == 1
    assert result.items[0].id == 9
    assert result.items[0].patient_id == 88
    assert str(result.items[0].appointment_date) == "2026-06-26"
    assert result.items[0].slot == 1
    assert result.items[0].status == 0
    assert result.items[0].payment_status == 1
    assert result.items[0].doctor_id == 3
    assert result.items[0].dept_sub_id == 4


async def test_query_filters_requested_registration_id():
    client = FakeClient(
        {
            "result": {
                "registrations": [
                    {"registrationId": 7, "date": "2026-06-20"},
                    {"registrationId": 9, "date": "2026-06-26"},
                ]
            }
        }
    )
    service = RegistrationService(client)

    result = await service.query(
        RegistrationQueryRequest(patient_id=88, registration_id=9)
    )

    assert [item.id for item in result.items] == [9]


async def test_query_reads_top_level_hms_select_detail_payload():
    client = FakeClient(
        {
            "registrations": [
                {
                    "registrationId": 13,
                    "date": "2026-06-26",
                    "slot": 1,
                    "status": 0,
                    "paymentStatus": 1,
                }
            ],
            "patientInfo": {"patientId": 1, "name": "张伟"},
        }
    )
    service = RegistrationService(client)

    result = await service.query(RegistrationQueryRequest(patient_id=1))

    assert [item.id for item in result.items] == [13]


async def test_query_recent_reads_top_level_hms_select_detail_payload():
    client = FakeClient(
        {
            "registrations": [
                {"registrationId": 1, "date": "2026-06-14"},
                {"registrationId": 38, "date": "2026-07-02"},
                {"registrationId": 30, "date": "2026-06-29"},
            ]
        }
    )
    service = RegistrationService(client)

    result = await service.query_recent(patient_id=1, limit=2)

    assert [item["registrationId"] for item in result] == [38, 30]
