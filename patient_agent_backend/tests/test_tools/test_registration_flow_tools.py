import json
from datetime import date

import pytest

from app.agent.request_context import set_patient_session, set_thread_id
from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store
from app.hms_client.models import ScheduleDetailResponse, ScheduleItem
from app.tools.doctor_tools import create_doctor_tools


class FakeDoctorService:
    def __init__(self):
        self.last_schedule_request = None
        self.schedule_requests = []

    async def schedule_detail(self, request):
        return ScheduleDetailResponse(
            work_plan_id=request.work_plan_id,
            doctor_id=3,
            doctor_name="张医生",
            dept_sub_id=4,
            date="2026-06-26",
            maximum=10,
            num=3,
            schedules=[
                ScheduleItem(
                    id=2,
                    work_plan_id=request.work_plan_id,
                    slot=1,
                    maximum=10,
                    num=3,
                )
            ],
        )

    async def schedules(self, request):
        self.last_schedule_request = request
        self.schedule_requests.append(request)
        return type("Schedules", (), {"items": []})()


class FakeHmsClient:
    def __init__(self):
        self.doctor_service = FakeDoctorService()


@pytest.mark.asyncio
async def test_query_schedule_detail_sets_pending_confirmation_flow_state():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    set_patient_session(type("Session", (), {"patient_id": 88})())
    set_thread_id("thread-1")
    tools = create_doctor_tools(FakeHmsClient())
    query_schedule_detail = next(tool for tool in tools if tool.name == "query_schedule_detail")

    result = await query_schedule_detail.ainvoke({"work_plan_id": 11})

    payload = json.loads(result)
    assert payload["ok"] is True
    assert store._data["patient:88:thread-1"].pending_registration_confirmation == {
        "work_plan_id": 11,
        "doctor_schedule_id": 2,
        "doctor_id": 3,
        "dept_sub_id": 4,
        "appointment_date": "2026-06-26",
        "slot": 1,
        "doctor_name": "张医生",
        "schedule_options": [
            {
                "doctor_schedule_id": 2,
                "slot": 1,
            }
        ],
    }


@pytest.mark.asyncio
async def test_query_doctor_schedules_defaults_date_when_omitted(monkeypatch):
    fake_client = FakeHmsClient()
    tools = create_doctor_tools(fake_client)
    query_doctor_schedules = next(tool for tool in tools if tool.name == "query_doctor_schedules")

    async def fake_resolve_sub_dept(hms_client, dept_name):
        return type("ResolveResult", (), {
            "error": None,
            "found": True,
            "items": [type("SubDept", (), {"id": 1})()],
        })()

    async def fake_resolve_doctor(hms_client, doctor_name=None, dept_name=None):
        return type("ResolveResult", (), {
            "error": None,
            "found": True,
            "items": [type("Doctor", (), {"id": 19, "model_dump": lambda self: {"id": 19}})()],
        })()

    monkeypatch.setattr("app.tools.doctor_tools.resolve_sub_dept", fake_resolve_sub_dept)
    monkeypatch.setattr("app.tools.doctor_tools.resolve_doctor", fake_resolve_doctor)

    await query_doctor_schedules.ainvoke({"doctor_name": "袁文斌", "dept_name": "口腔科"})

    assert fake_client.doctor_service.last_schedule_request.date == date.today().isoformat()


@pytest.mark.asyncio
async def test_query_schedule_detail_recovers_missing_confirmation_fields_from_schedule_query(
    monkeypatch,
):
    class IncompleteDetailDoctorService(FakeDoctorService):
        async def schedule_detail(self, request):
            return ScheduleDetailResponse(
                work_plan_id=request.work_plan_id,
                doctor_id=19,
                doctor_name="袁文斌",
                dept_sub_id=None,
                date=None,
                maximum=10,
                num=0,
                schedules=[
                    ScheduleItem(
                        id=951,
                        work_plan_id=request.work_plan_id,
                        slot=1,
                        maximum=0,
                        num=0,
                    )
                ],
            )

        async def schedules(self, request):
            self.last_schedule_request = request
            return type(
                "Schedules",
                (),
                {
                    "items": [
                        {
                            "doctorId": 19,
                            "doctorName": "袁文斌",
                            "workPlanId": 11,
                            "maximum": 10,
                            "slot": [True, False, False],
                        }
                    ]
                },
            )()

    class IncompleteDetailHmsClient:
        def __init__(self):
            self.doctor_service = IncompleteDetailDoctorService()

    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    set_patient_session(type("Session", (), {"patient_id": 88})())
    set_thread_id("thread-2")
    fake_client = IncompleteDetailHmsClient()
    tools = create_doctor_tools(fake_client)
    query_doctor_schedules = next(tool for tool in tools if tool.name == "query_doctor_schedules")
    query_schedule_detail = next(tool for tool in tools if tool.name == "query_schedule_detail")

    async def fake_resolve_sub_dept(hms_client, dept_name):
        return type("ResolveResult", (), {
            "error": None,
            "found": True,
            "items": [type("SubDept", (), {"id": 4})()],
        })()

    async def fake_resolve_doctor(hms_client, doctor_name=None, dept_name=None):
        return type("ResolveResult", (), {
            "error": None,
            "found": True,
            "items": [type("Doctor", (), {"id": 19, "model_dump": lambda self: {"id": 19}})()],
        })()

    monkeypatch.setattr("app.tools.doctor_tools.resolve_sub_dept", fake_resolve_sub_dept)
    monkeypatch.setattr("app.tools.doctor_tools.resolve_doctor", fake_resolve_doctor)

    await query_doctor_schedules.ainvoke(
        {"doctor_name": "袁文斌", "dept_name": "口腔科", "date": "2026-06-28"}
    )
    result = await query_schedule_detail.ainvoke({"work_plan_id": 11})

    payload = json.loads(result)
    assert payload["ok"] is True
    assert store._data["patient:88:thread-2"].pending_registration_confirmation == {
        "work_plan_id": 11,
        "doctor_schedule_id": 951,
        "doctor_id": 19,
        "dept_sub_id": 4,
        "appointment_date": "2026-06-28",
        "slot": 1,
        "doctor_name": "袁文斌",
        "schedule_options": [
            {
                "doctor_schedule_id": 951,
                "slot": 1,
            }
        ],
    }


@pytest.mark.asyncio
async def test_query_doctor_schedules_falls_back_to_sub_dept_lookup_when_doctor_only(
    monkeypatch,
):
    class DoctorOnlyScheduleService(FakeDoctorService):
        async def schedules(self, request):
            self.last_schedule_request = request
            self.schedule_requests.append(request)
            if request.dept_sub_id is None:
                raise ValueError("请求参数错误: dept_sub_id 不能为空")
            return type(
                "Schedules",
                (),
                {
                    "items": [
                        {
                            "doctorId": request.doctor_id,
                            "doctorName": "韩倩倩",
                            "workPlanId": 21,
                            "maximum": 10,
                            "slot": [True, False, False],
                        }
                    ]
                },
            )()

    class DoctorOnlyDeptService:
        async def list_depts(self, request):
            return type(
                "DeptListResponse",
                (),
                {"items": [type("Dept", (), {"id": 1, "name": "口腔科"})()]},
            )()

        async def detail(self, request):
            return type(
                "DeptDetailResponse",
                (),
                {"sub_depts": [type("SubDept", (), {"id": 8, "name": "口腔科"})()]},
            )()

    class DoctorOnlyHmsClient:
        def __init__(self):
            self.doctor_service = DoctorOnlyScheduleService()
            self.dept_service = DoctorOnlyDeptService()

    async def fake_resolve_doctor(hms_client, doctor_name=None, dept_name=None):
        return type(
            "ResolveResult",
            (),
            {
                "error": None,
                "found": True,
                "items": [
                    type("Doctor", (), {"id": 19, "model_dump": lambda self: {"id": 19}})()
                ],
            },
        )()

    monkeypatch.setattr("app.tools.doctor_tools.resolve_doctor", fake_resolve_doctor)
    fake_client = DoctorOnlyHmsClient()
    tools = create_doctor_tools(fake_client)
    query_doctor_schedules = next(tool for tool in tools if tool.name == "query_doctor_schedules")

    result = await query_doctor_schedules.ainvoke({"doctor_name": "韩倩倩", "date": "今天上午"})

    payload = json.loads(result)
    assert payload["ok"] is True
    assert fake_client.doctor_service.schedule_requests[0].dept_sub_id == 8
    assert fake_client.doctor_service.schedule_requests[0].date == date.today().isoformat()


@pytest.mark.asyncio
async def test_query_doctor_schedules_checks_all_matching_sub_depts_for_doctor_and_dept(
    monkeypatch,
):
    class DoctorDeptScheduleService(FakeDoctorService):
        async def schedules(self, request):
            self.last_schedule_request = request
            self.schedule_requests.append(request)
            if request.dept_sub_id == 9:
                return type(
                    "Schedules",
                    (),
                    {
                        "items": [
                            {
                                "doctorId": request.doctor_id,
                                "doctorName": "王文彦",
                                "workPlanId": 240,
                                "maximum": 10,
                                "slot": [True, True, False],
                            }
                        ]
                    },
                )()
            return type("Schedules", (), {"items": []})()

    class DoctorDeptHmsClient:
        def __init__(self):
            self.doctor_service = DoctorDeptScheduleService()

    async def fake_resolve_sub_dept(hms_client, dept_name):
        return type(
            "ResolveResult",
            (),
            {
                "error": None,
                "found": True,
                "items": [
                    type("SubDept", (), {"id": 8})(),
                    type("SubDept", (), {"id": 9})(),
                ],
            },
        )()

    async def fake_resolve_doctor(hms_client, doctor_name=None, dept_name=None):
        return type(
            "ResolveResult",
            (),
            {
                "error": None,
                "found": True,
                "items": [
                    type("Doctor", (), {"id": 3, "model_dump": lambda self: {"id": 3}})()
                ],
            },
        )()

    monkeypatch.setattr("app.tools.doctor_tools.resolve_sub_dept", fake_resolve_sub_dept)
    monkeypatch.setattr("app.tools.doctor_tools.resolve_doctor", fake_resolve_doctor)
    fake_client = DoctorDeptHmsClient()
    tools = create_doctor_tools(fake_client)
    query_doctor_schedules = next(tool for tool in tools if tool.name == "query_doctor_schedules")

    result = await query_doctor_schedules.ainvoke(
        {"doctor_name": "王文彦", "dept_name": "内科", "date": "2026-07-01"}
    )

    payload = json.loads(result)
    assert payload["ok"] is True
    assert [request.dept_sub_id for request in fake_client.doctor_service.schedule_requests] == [8, 9]
    assert payload["data"][0]["workPlanId"] == 240
