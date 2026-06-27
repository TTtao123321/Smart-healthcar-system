"""医生/排班服务 — 对接 HMS 医生和排班相关 API"""

import logging
from typing import TYPE_CHECKING

from app.hms_client.models import (
    DoctorDetailResponse,
    DoctorItem,
    DoctorListRequest,
    DoctorListResponse,
    ScheduleDetailRequest,
    ScheduleDetailResponse,
    ScheduleItem,
    ScheduleListRequest,
    ScheduleListResponse,
)

if TYPE_CHECKING:
    from app.hms_client.client import HmsClient

logger = logging.getLogger(__name__)


class DoctorService:
    """医生/排班服务"""

    def __init__(self, client: "HmsClient"):
        self._client = client

    async def list_doctors(self, request: DoctorListRequest | None = None) -> DoctorListResponse:
        """查询医生列表

        对接 HMS: POST /doctor/selectConditionByPage
        """
        if request is None:
            request = DoctorListRequest()

        payload = {
            "page": request.page,
            "length": request.page_size,
            "status": 1,  # 1=在职，必填字段
        }
        if request.name:
            payload["name"] = request.name
        if request.dept_sub_id:
            payload["deptSubId"] = request.dept_sub_id

        data = await self._client.post("/doctor/selectConditionByPage", json=payload)

        result = data.get("result", {})
        items = []
        for item in result.get("list", []):
            items.append(DoctorItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
                sex=item.get("sex"),
                photo=item.get("photo"),
                job=item.get("job"),
                degree=item.get("degree"),
                school=item.get("school"),
                description=item.get("description"),
                tag=item.get("tag"),
                recommended=item.get("recommended"),
                status=item.get("status"),
            ))

        return DoctorListResponse(
            total=result.get("totalCount", 0) if isinstance(result, dict) else len(items),
            items=items,
        )

    async def detail(self, doctor_id: int) -> DoctorDetailResponse:
        """查询医生详情

        对接 HMS: POST /doctor/selectDoctorDetailById
        """
        data = await self._client.post(
            "/doctor/selectDoctorDetailById",
            json={"id": doctor_id},
        )

        doctor = data.get("doctor", data.get("result", {}))
        return DoctorDetailResponse(
            id=doctor.get("id", 0),
            name=doctor.get("name", ""),
            sex=doctor.get("sex"),
            photo=doctor.get("photo"),
            birthday=doctor.get("birthday"),
            school=doctor.get("school"),
            degree=doctor.get("degree"),
            tel=doctor.get("tel"),
            address=doctor.get("address"),
            email=doctor.get("email"),
            job=doctor.get("job"),
            remark=doctor.get("remark"),
            description=doctor.get("description"),
            hiredate=doctor.get("hiredate"),
            tag=doctor.get("tag"),
            recommended=doctor.get("recommended"),
            status=doctor.get("status"),
        )

    async def list_by_sub_dept(self, dept_sub_id: int) -> list[DoctorItem]:
        """根据诊室查询医生

        对接 HMS: POST /doctor/selectDoctorsBySubId
        """
        data = await self._client.post(
            "/doctor/selectDoctorsBySubId",
            json={"deptSubId": dept_sub_id},
        )

        items = []
        for item in data.get("result", []):
            items.append(DoctorItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
                sex=item.get("sex"),
                photo=item.get("photo"),
                job=item.get("job"),
                degree=item.get("degree"),
                school=item.get("school"),
                description=item.get("description"),
                tag=item.get("tag"),
                recommended=item.get("recommended"),
                status=item.get("status"),
            ))
        return items

    async def schedules(self, request: ScheduleListRequest) -> ScheduleListResponse:
        """查询医生排班

        对接 HMS: POST /doctor/work_plan/schedule/selectDoctorScheduleByDeptSubIdAndDate
        """
        payload = {}
        if request.dept_sub_id:
            payload["deptSubId"] = request.dept_sub_id
        if request.date:
            payload["date"] = request.date
        if request.doctor_id:
            payload["doctorId"] = request.doctor_id

        data = await self._client.post(
            "/doctor/work_plan/schedule/selectDoctorScheduleByDeptSubIdAndDate",
            json=payload,
        )

        items = data.get("result", [])
        return ScheduleListResponse(items=items if isinstance(items, list) else [items])

    async def schedule_detail(self, request: ScheduleDetailRequest) -> ScheduleDetailResponse:
        """查询排班详情

        对接 HMS: POST /doctor/work_plan/schedule/selectScheduleByWorkPlanId
        """
        data = await self._client.post(
            "/doctor/work_plan/schedule/selectScheduleByWorkPlanId",
            json={"workPlanId": request.work_plan_id},
        )

        result = data.get("result", {})
        schedules = []
        raw_schedules = result.get("schedules")
        if raw_schedules is None:
            raw_schedules = result.get("scheduleList")
        if raw_schedules is None:
            raw_schedules = result.get("slots", [])

        for s in raw_schedules:
            schedules.append(ScheduleItem(
                id=s.get("id", s.get("scheduleId", 0)),
                work_plan_id=s.get("workPlanId", s.get("work_plan_id", 0)),
                slot=s.get("slot", 0),
                maximum=s.get("maximum", result.get("maximum", 0)),
                num=s.get("num", 0),
            ))

        return ScheduleDetailResponse(
            work_plan_id=request.work_plan_id,
            doctor_id=result.get("doctorId", result.get("doctor_id")),
            doctor_name=result.get("doctorName", result.get("doctor_name")),
            dept_sub_id=result.get("deptSubId", result.get("dept_sub_id")),
            date=result.get("date"),
            maximum=result.get("maximum", 0),
            num=result.get("num", 0),
            schedules=schedules,
        )
