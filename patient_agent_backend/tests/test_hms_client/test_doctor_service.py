from app.hms_client.models import ScheduleDetailRequest
from app.hms_client.services.doctor_service import DoctorService


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.requests = []

    async def post(self, path: str, json: dict | None = None):
        self.requests.append({"path": path, "json": json})
        return self.response


async def test_schedule_detail_reads_hms_slots_payload():
    client = FakeClient(
        {
            "result": {
                "doctorId": 19,
                "maximum": 10,
                "date": "2026-06-28",
                "slots": [
                    {"scheduleId": 951, "slot": 1, "num": 0},
                    {"scheduleId": 952, "slot": 2, "num": 1},
                ],
            }
        }
    )
    service = DoctorService(client)

    result = await service.schedule_detail(ScheduleDetailRequest(work_plan_id=217))

    assert client.requests == [
        {
            "path": "/doctor/work_plan/schedule/selectScheduleByWorkPlanId",
            "json": {"workPlanId": 217},
        }
    ]
    assert result.work_plan_id == 217
    assert result.doctor_id == 19
    assert result.date == "2026-06-28"
    assert [item.id for item in result.schedules] == [951, 952]
    assert [item.slot for item in result.schedules] == [1, 2]
    assert [item.maximum for item in result.schedules] == [10, 10]
    assert [item.num for item in result.schedules] == [0, 1]
