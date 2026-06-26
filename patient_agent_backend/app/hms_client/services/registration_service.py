"""挂号服务 — 对接 HMS 挂号相关 API"""

import logging
from typing import TYPE_CHECKING

from app.hms_client.models import (
    RegistrationCancelRequest,
    RegistrationCancelResponse,
    RegistrationCreateRequest,
    RegistrationCreateResponse,
    RegistrationItem,
    RegistrationQueryRequest,
    RegistrationQueryResponse,
)

if TYPE_CHECKING:
    from app.hms_client.client import HmsClient

logger = logging.getLogger(__name__)


class RegistrationService:
    """挂号服务"""

    def __init__(self, client: "HmsClient"):
        self._client = client

    async def create(self, request: RegistrationCreateRequest) -> RegistrationCreateResponse:
        """创建挂号预约

        对接 HMS: POST /medical_registration/save
        """
        data = await self._client.post(
            "/medical_registration/save",
            json={
                "patientId": request.patient_id,
                "workPlanId": request.work_plan_id,
                "doctorScheduleId": request.doctor_schedule_id,
                "doctorId": request.doctor_id,
                "deptSubId": request.dept_sub_id,
                "date": request.appointment_date.isoformat(),
                "slot": request.slot,
            },
        )

        result = data.get("result", data)
        return RegistrationCreateResponse(
            id=result.get("id", 0),
            status=result.get("status", 0),
        )

    async def query(self, request: RegistrationQueryRequest) -> RegistrationQueryResponse:
        """查询挂号状态

        对接 HMS: POST /patient/selectDetail
        """
        data = await self._client.post(
            "/patient/selectDetail",
            json={"patientId": request.patient_id},
        )

        result = data.get("result", data)
        items = []
        for item in result.get("registrations", []):
            registration_id = item.get("registrationId", item.get("id", 0))
            if request.registration_id and registration_id != request.registration_id:
                continue
            items.append(RegistrationItem(
                id=registration_id,
                patient_id=item.get("patientId", request.patient_id),
                work_plan_id=item.get("workPlanId"),
                doctor_schedule_id=item.get("doctorScheduleId"),
                doctor_id=item.get("doctorId"),
                dept_sub_id=item.get("deptSubId"),
                appointment_date=item.get("date"),
                slot=item.get("slot"),
                status=item.get("status"),
                payment_status=item.get("paymentStatus"),
                create_time=item.get("createTime"),
            ))

        return RegistrationQueryResponse(items=items)

    async def query_recent(self, patient_id: int, limit: int = 3) -> list[dict]:
        """查询患者最近就诊记录

        对接 HMS: POST /patient/selectDetail
        """
        data = await self._client.post(
            "/patient/selectDetail",
            json={"patientId": patient_id},
        )

        result = data.get("result", data)
        registrations = result.get("registrations", [])
        registrations.sort(key=lambda item: item.get("date", ""), reverse=True)
        return registrations[:limit]

    async def cancel(self, request: RegistrationCancelRequest) -> RegistrationCancelResponse:
        """取消挂号

        对接 HMS: POST /patient/updateRegistrationStatus
        """
        data = await self._client.post(
            "/patient/updateRegistrationStatus",
            json={"id": request.registration_id, "status": -1},
        )

        result = data.get("result", 0)
        return RegistrationCancelResponse(result=result if isinstance(result, int) else 0)
