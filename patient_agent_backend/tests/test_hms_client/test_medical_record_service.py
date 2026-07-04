from app.hms_client.services.medical_record_service import MedicalRecordService


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.requests = []

    async def post(self, path: str, json: dict | None = None):
        self.requests.append({"path": path, "json": json})
        return self.response


async def test_query_patient_records_posts_patient_scoped_payload_and_maps_items():
    client = FakeClient(
        {
            "result": [
                {
                    "medicalRecordId": 101,
                    "visitDate": "2026-07-01",
                    "department": "呼吸内科",
                    "doctorName": "张医生",
                    "chiefComplaintSummary": "咳嗽 3 天",
                    "status": "RECORD_READY",
                }
            ]
        }
    )
    service = MedicalRecordService(client)

    result = await service.query_patient_records(
        patient_id=7,
        start_date="2026-06-01",
        end_date="2026-07-01",
    )

    assert client.requests == [
        {
            "path": "/patient/medical-records",
            "json": {
                "patientId": 7,
                "startDate": "2026-06-01",
                "endDate": "2026-07-01",
            },
        }
    ]
    assert len(result.items) == 1
    assert result.items[0].medicalRecordId == 101
    assert result.items[0].department == "呼吸内科"
    assert result.items[0].chiefComplaintSummary == "咳嗽 3 天"


async def test_get_detail_maps_patient_visible_detail_fields():
    client = FakeClient(
        {
            "result": {
                "medicalRecordId": 101,
                "visitDate": "2026-07-01",
                "department": "呼吸内科",
                "doctorName": "张医生",
                "chiefComplaint": "咳嗽 3 天",
                "diagnosisSummary": "上呼吸道感染",
                "instructionSummary": "清淡饮食",
            }
        }
    )
    service = MedicalRecordService(client)

    result = await service.get_detail(patient_id=7, medical_record_id=101)

    assert client.requests == [
        {
            "path": "/patient/medical-records/detail",
            "json": {"patientId": 7, "medicalRecordId": 101},
        }
    ]
    assert result.medicalRecordId == 101
    assert result.diagnosisSummary == "上呼吸道感染"
    assert result.instructionSummary == "清淡饮食"
