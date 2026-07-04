from app.hms_client.services.prescription_service import PrescriptionService


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.requests = []

    async def post(self, path: str, json: dict | None = None):
        self.requests.append({"path": path, "json": json})
        return self.response


async def test_query_patient_prescriptions_posts_patient_scoped_payload_and_maps_items():
    client = FakeClient(
        {
            "result": [
                {
                    "prescriptionId": 18,
                    "medicalRecordId": 101,
                    "visitDate": "2026-07-01",
                    "department": "呼吸内科",
                    "doctorName": "张医生",
                    "type": 1,
                    "status": 2,
                }
            ]
        }
    )
    service = PrescriptionService(client)

    result = await service.query_patient_prescriptions(
        patient_id=7,
        start_date="2026-06-01",
        end_date="2026-07-01",
    )

    assert client.requests == [
        {
            "path": "/patient/prescriptions",
            "json": {
                "patientId": 7,
                "startDate": "2026-06-01",
                "endDate": "2026-07-01",
            },
        }
    ]
    assert len(result.items) == 1
    assert result.items[0].prescriptionId == 18
    assert result.items[0].department == "呼吸内科"


async def test_get_detail_maps_prescription_items():
    client = FakeClient(
        {
            "result": {
                "prescriptionId": 18,
                "medicalRecordId": 101,
                "visitDate": "2026-07-01",
                "department": "呼吸内科",
                "doctorName": "张医生",
                "doctorAdvice": "清淡饮食",
                "items": [
                    {
                        "id": 1,
                        "prescriptionId": 18,
                        "drugName": "阿莫西林胶囊",
                        "quantity": 2,
                        "dosage": "一次 1 粒",
                    }
                ],
            }
        }
    )
    service = PrescriptionService(client)

    result = await service.get_detail(patient_id=7, prescription_id=18)

    assert client.requests == [
        {
            "path": "/patient/prescriptions/detail",
            "json": {"patientId": 7, "prescriptionId": 18},
        }
    ]
    assert result.prescriptionId == 18
    assert result.doctorAdvice == "清淡饮食"
    assert len(result.items) == 1
    assert result.items[0].drugName == "阿莫西林胶囊"
