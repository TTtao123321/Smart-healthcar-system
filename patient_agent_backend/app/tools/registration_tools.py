"""挂号工具"""

import logging
from datetime import date as date_type

from langchain_core.tools import tool

from app.agent.request_context import get_patient_id, get_thread_id
from app.chat.flow_state import get_flow_state_store
from app.hms_client import HmsClient
from app.hms_client.models import (
    RegistrationCancelRequest,
    RegistrationCreateRequest,
    RegistrationQueryRequest,
)
from app.tools.tool_response import empty, err, ok

logger = logging.getLogger(__name__)


def _require_session_patient_id() -> int:
    """从当前请求上下文读取真实患者身份"""
    patient_id = get_patient_id()
    if patient_id is None:
        raise ValueError("请先登录后再挂号")
    return int(patient_id)


def _build_flow_state_key(patient_id: int) -> str:
    thread_id = get_thread_id()
    if not thread_id:
        raise ValueError("当前对话线程不存在，请重新发起挂号流程")
    return f"patient:{patient_id}:{thread_id}"


def create_registration_tools(hms_client: HmsClient):
    """创建挂号相关工具（闭包注入 hms_client）"""

    async def _load_owned_registration(registration_id: int, patient_id: int):
        result = await hms_client.registration_service.query(
            RegistrationQueryRequest(
                patient_id=patient_id,
                registration_id=registration_id,
            )
        )
        items = result.items if hasattr(result, "items") else []
        return items[0] if items else None

    @tool
    async def create_registration(
        work_plan_id: int,
        doctor_schedule_id: int,
        doctor_id: int,
        dept_sub_id: int,
        appointment_date: str,
        slot: int,
    ) -> str:
        """创建挂号预约。
        当患者明确确认要挂号时使用此工具。调用前必须先通过 query_doctor_schedules
        和 query_schedule_detail 获取真实的 work_plan_id、doctor_schedule_id 等字段。

        work_plan_id: 出诊计划ID（必须来自 query_doctor_schedules 返回结果）
        doctor_schedule_id: 排班时段ID（必须来自 query_schedule_detail 返回结果）
        doctor_id: 医生ID（必须来自工具返回结果）
        dept_sub_id: 诊室ID（必须来自工具返回结果）
        appointment_date: 就诊日期，格式 YYYY-MM-DD
        slot: 时段编号（必须来自 query_schedule_detail 返回结果）

        返回格式：{"ok": true, "summary": "...", "data": {...}}
        """
        try:
            patient_id = _require_session_patient_id()
        except ValueError as e:
            return err(
                str(e),
                "请先引导用户完成登录，再继续挂号流程。",
            )

        try:
            flow_state = await get_flow_state_store().load(_build_flow_state_key(patient_id))
        except ValueError as e:
            return err(
                str(e),
                "请引导用户重新开始挂号流程。",
            )

        pending_confirmation = flow_state.pending_registration_confirmation
        if pending_confirmation is None:
            return err(
                "请先确认挂号信息",
                "请先向用户展示待确认挂号信息，收到明确确认后再创建挂号。",
            )

        try:
            appt_date = date_type.fromisoformat(appointment_date)
        except ValueError:
            return err(
                f"appointment_date 格式错误: {appointment_date}",
                "日期必须是 YYYY-MM-DD 格式，请引导用户提供正确日期。",
            )

        try:
            result = await hms_client.registration_service.create(
                RegistrationCreateRequest(
                    patient_id=patient_id,
                    work_plan_id=work_plan_id,
                    doctor_schedule_id=doctor_schedule_id,
                    doctor_id=doctor_id,
                    dept_sub_id=dept_sub_id,
                    appointment_date=appt_date,
                    slot=slot,
                )
            )
        except Exception as e:
            logger.error(f"create_registration 调用 HMS 失败: {e}")
            return err(
                f"挂号失败: {e}",
                "请告知用户挂号失败，建议稍后再试或转人工客服。",
            )

        await get_flow_state_store().delete(_build_flow_state_key(patient_id))

        return ok("挂号成功", result.model_dump())

    @tool
    async def query_registration(
        registration_id: int | None = None,
    ) -> str:
        """查询挂号记录。
        当患者询问"我的挂号""挂号记录"时使用此工具。

        registration_id: 挂号记录ID（可选，查询某条特定记录）

        返回格式：{"ok": true, "summary": "...", "data": [...]}
        """
        try:
            patient_id = _require_session_patient_id()
        except ValueError:
            return err(
                "请先登录后再查询挂号记录",
                "若用户已登录，优先按当前登录患者查询挂号记录。",
            )

        try:
            result = await hms_client.registration_service.query(
                RegistrationQueryRequest(
                    patient_id=patient_id,
                    registration_id=registration_id,
                )
            )
        except Exception as e:
            logger.error(f"query_registration 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )

        items = result.items if hasattr(result, "items") else []
        if not items:
            return empty("暂无挂号记录")

        return ok(f"共找到 {len(items)} 条挂号记录", [i.model_dump() for i in items])

    @tool
    async def cancel_registration(registration_id: int) -> str:
        """取消挂号。
        当患者明确要求取消某条挂号时使用此工具。

        registration_id: 要取消的挂号记录ID（必须来自 query_registration 返回结果）

        返回格式：{"ok": true, "summary": "...", "data": {...}}
        """
        try:
            patient_id = _require_session_patient_id()
        except ValueError as e:
            return err(
                str(e),
                "请先引导用户完成登录，再继续取消挂号流程。",
            )

        try:
            item = await _load_owned_registration(registration_id, patient_id)
            if item is None:
                return err(
                    "记录不存在或无权限",
                    "请告知用户只能取消本人挂号记录。",
                )
            result = await hms_client.registration_service.cancel(
                RegistrationCancelRequest(registration_id=registration_id)
            )
        except Exception as e:
            logger.error(f"cancel_registration 调用 HMS 失败: {e}")
            return err(
                f"取消挂号失败: {e}",
                "请告知用户取消失败，建议稍后再试。",
            )

        return ok("挂号已取消", result.model_dump())

    return [create_registration, query_registration, cancel_registration]
