"""医生/排班查询工具"""

from langchain_core.tools import tool

from app.hms_client import HmsClient
from app.hms_client.models import DoctorListRequest, ScheduleListRequest, ScheduleDetailRequest


def create_doctor_tools(hms_client: HmsClient):
    """创建医生/排班相关工具（闭包注入 hms_client）"""

    @tool
    async def query_doctors(
        name: str | None = None,
        dept_sub_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> str:
        """按科室/姓名查询医生列表。
        当患者询问"XX科室有哪些医生""XX医生在不在"时使用此工具。
        name: 医生姓名（可选）
        dept_sub_id: 诊室ID（可选）"""
        result = await hms_client.doctor_service.list_doctors(
            DoctorListRequest(
                name=name,
                dept_sub_id=dept_sub_id,
                page=page,
                page_size=page_size,
            )
        )
        return result.model_dump_json()

    @tool
    async def query_doctor_detail(doctor_id: int) -> str:
        """查询医生详细信息，包括职称、学历、擅长领域等。
        当患者想了解某位医生的详细信息时使用此工具。"""
        result = await hms_client.doctor_service.detail(doctor_id)
        return result.model_dump_json()

    @tool
    async def query_doctor_schedules(
        dept_sub_id: int | None = None,
        date: str | None = None,
        doctor_id: int | None = None,
    ) -> str:
        """查询医生排班与号源状态。
        当患者询问"某天有哪些医生出诊""XX医生什么时候出诊"时使用此工具。
        dept_sub_id: 诊室ID（可选）
        date: 日期，格式 YYYY-MM-DD（可选）
        doctor_id: 医生ID（可选）"""
        result = await hms_client.doctor_service.schedules(
            ScheduleListRequest(
                dept_sub_id=dept_sub_id,
                date=date,
                doctor_id=doctor_id,
            )
        )
        return result.model_dump_json()

    @tool
    async def query_schedule_detail(work_plan_id: int) -> str:
        """查询排班详情，包含各时段号源情况。
        当患者想了解某个排班的具体时段和剩余号源时使用此工具。"""
        result = await hms_client.doctor_service.schedule_detail(
            ScheduleDetailRequest(work_plan_id=work_plan_id)
        )
        return result.model_dump_json()

    return [query_doctors, query_doctor_detail, query_doctor_schedules, query_schedule_detail]
