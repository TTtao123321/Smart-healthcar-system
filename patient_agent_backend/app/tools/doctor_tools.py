"""医生/排班查询工具"""

import logging

from langchain_core.tools import tool

from app.hms_client import HmsClient
from app.hms_client.models import ScheduleDetailRequest, ScheduleListRequest
from app.tools.name_resolver import resolve_doctor, resolve_sub_dept
from app.tools.tool_response import empty, err, ok

logger = logging.getLogger(__name__)


def create_doctor_tools(hms_client: HmsClient):
    """创建医生/排班相关工具（闭包注入 hms_client）"""

    @tool
    async def query_doctors(
        dept_name: str | None = None,
        doctor_name: str | None = None,
    ) -> str:
        """按科室名/医生姓名查询医生列表。
        当患者询问"内科有哪些医生""XX医生在不在"时使用此工具。

        dept_name: 科室名称（如"内科"，可选，支持模糊匹配）
        doctor_name: 医生姓名（可选，支持模糊匹配）
        注意：dept_name 和 doctor_name 至少提供一个。

        返回格式：{"ok": true, "summary": "...", "data": [{"id": int, "name": str, "job": str, ...}]}
        """
        if not dept_name and not doctor_name:
            return err(
                "未提供科室名称或医生姓名",
                "请引导用户提供具体的科室或医生姓名。",
            )

        resolve_result = await resolve_doctor(
            hms_client, doctor_name=doctor_name, dept_name=dept_name
        )
        if resolve_result.error:
            return err(
                f"查询医生失败: {resolve_result.error}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )
        if not resolve_result.found:
            keyword = " / ".join(filter(None, [dept_name, doctor_name]))
            return empty(f"未找到匹配「{keyword}」的医生")

        data = [d.model_dump() for d in resolve_result.items]
        return ok(f"共找到 {len(data)} 位医生", data)

    @tool
    async def query_doctor_schedules(
        doctor_name: str | None = None,
        dept_name: str | None = None,
        date: str | None = None,
    ) -> str:
        """查询医生排班与号源状态。
        当患者询问"XX医生什么时候出诊""内科明天有哪些医生"时使用此工具。

        doctor_name: 医生姓名（可选）
        dept_name: 科室名称（可选）
        date: 日期，格式 YYYY-MM-DD（可选，不传则查近期）
        注意：doctor_name 和 dept_name 至少提供一个。

        返回格式：{"ok": true, "summary": "...", "data": [...]}
        """
        if not doctor_name and not dept_name:
            return err(
                "未提供医生姓名或科室名称",
                "请引导用户告知具体医生或科室。",
            )

        # 解析 dept_sub_id 列表
        sub_dept_ids: list[int] = []
        if dept_name:
            sub_result = await resolve_sub_dept(hms_client, dept_name)
            if sub_result.error:
                return err(
                    f"查询科室失败: {sub_result.error}",
                    "请告知用户系统暂时无法查询，请稍后再试。",
                )
            if not sub_result.found:
                return empty(f"未找到科室「{dept_name}」")
            sub_dept_ids = [s.id for s in sub_result.items]

        # 解析 doctor_id
        doctor_id: int | None = None
        if doctor_name:
            doctor_result = await resolve_doctor(
                hms_client, doctor_name=doctor_name, dept_name=dept_name
            )
            if doctor_result.error:
                return err(
                    f"查询医生失败: {doctor_result.error}",
                    "请告知用户系统暂时无法查询，请稍后再试。",
                )
            if not doctor_result.found:
                return empty(f"未找到医生「{doctor_name}」")
            if len(doctor_result.items) > 1:
                data = [d.model_dump() for d in doctor_result.items]
                return ok(
                    f"匹配到 {len(data)} 位医生，请引导用户选择具体医生",
                    data,
                )
            doctor_id = doctor_result.items[0].id

        # 查询排班
        all_schedules: list = []
        try:
            if sub_dept_ids and doctor_id is None:
                for sid in sub_dept_ids:
                    resp = await hms_client.doctor_service.schedules(
                        ScheduleListRequest(dept_sub_id=sid, date=date)
                    )
                    all_schedules.extend(resp.items)
            else:
                resp = await hms_client.doctor_service.schedules(
                    ScheduleListRequest(
                        dept_sub_id=sub_dept_ids[0] if sub_dept_ids else None,
                        date=date,
                        doctor_id=doctor_id,
                    )
                )
                all_schedules.extend(resp.items)
        except Exception as e:
            logger.error(f"query_doctor_schedules 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )

        if not all_schedules:
            return empty("近期无排班数据")

        return ok(f"共找到 {len(all_schedules)} 条排班", all_schedules)

    @tool
    async def query_schedule_detail(work_plan_id: int) -> str:
        """查询某条排班的详情，包含各时段号源情况（用于挂号前选择时段）。

        work_plan_id: 排班 ID（必须从 query_doctor_schedules 返回结果中获取，不要编造）

        返回格式：{"ok": true, "summary": "...", "data": {...}}
        """
        try:
            result = await hms_client.doctor_service.schedule_detail(
                ScheduleDetailRequest(work_plan_id=work_plan_id)
            )
        except Exception as e:
            logger.error(f"query_schedule_detail 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )

        return ok("排班详情", result.model_dump())

    return [query_doctors, query_doctor_schedules, query_schedule_detail]
