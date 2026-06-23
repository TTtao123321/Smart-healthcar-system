"""挂号工具"""

from datetime import date as date_type

from langchain_core.tools import tool

from app.hms_client import HmsClient
from app.hms_client.models import (
    RegistrationCreateRequest,
    RegistrationQueryRequest,
    RegistrationCancelRequest,
)


def create_registration_tools(hms_client: HmsClient):
    """创建挂号相关工具（闭包注入 hms_client）"""

    @tool
    async def create_registration(
        patient_card_id: int,
        work_plan_id: int,
        doctor_schedule_id: int,
        doctor_id: int,
        dept_sub_id: int,
        appointment_date: str,
        slot: int,
    ) -> str:
        """创建挂号预约。
        当患者确认要挂号时使用此工具，需要提供完整的挂号信息。
        patient_card_id: 患者就诊卡ID
        work_plan_id: 医生出诊计划ID
        doctor_schedule_id: 医生排班时段ID
        doctor_id: 医生ID
        dept_sub_id: 诊室ID
        appointment_date: 就诊日期，格式 YYYY-MM-DD
        slot: 时间段编号"""
        result = await hms_client.registration_service.create(
            RegistrationCreateRequest(
                patient_card_id=patient_card_id,
                work_plan_id=work_plan_id,
                doctor_schedule_id=doctor_schedule_id,
                doctor_id=doctor_id,
                dept_sub_id=dept_sub_id,
                appointment_date=date_type.fromisoformat(appointment_date),
                slot=slot,
            )
        )
        return result.model_dump_json()

    @tool
    async def query_registration(
        patient_card_id: int | None = None,
        registration_id: int | None = None,
    ) -> str:
        """查询挂号状态。
        当患者想查看挂号记录或挂号状态时使用此工具。
        patient_card_id: 患者就诊卡ID（可选）
        registration_id: 挂号记录ID（可选）"""
        result = await hms_client.registration_service.query(
            RegistrationQueryRequest(
                patient_card_id=patient_card_id,
                registration_id=registration_id,
            )
        )
        return result.model_dump_json()

    @tool
    async def cancel_registration(registration_id: int) -> str:
        """取消挂号。
        当患者想要取消已有的挂号预约时使用此工具。
        registration_id: 挂号记录ID"""
        result = await hms_client.registration_service.cancel(
            RegistrationCancelRequest(registration_id=registration_id)
        )
        return result.model_dump_json()

    return [create_registration, query_registration, cancel_registration]
