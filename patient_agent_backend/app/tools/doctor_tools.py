"""医生/排班查询工具"""

import logging
from datetime import date as date_type

from langchain_core.tools import tool

from app.agent.request_context import get_patient_id, get_thread_id
from app.chat.flow_state import get_flow_state_store
from app.hms_client import HmsClient
from app.hms_client.models import ScheduleDetailRequest, ScheduleListRequest
from app.tools.name_resolver import resolve_doctor, resolve_sub_dept
from app.tools.tool_response import empty, err, ok

logger = logging.getLogger(__name__)


def _build_flow_state_key() -> str | None:
    patient_id = get_patient_id()
    thread_id = get_thread_id()
    if patient_id is None or not thread_id:
        return None
    return f"patient:{patient_id}:{thread_id}"


async def _save_pending_registration_confirmation(result) -> None:
    thread_key = _build_flow_state_key()
    if thread_key is None or not result.schedules:
        return

    selected_schedule = result.schedules[0]
    await get_flow_state_store().save(
        thread_key,
        {
            "pending_registration_confirmation": {
                "work_plan_id": result.work_plan_id,
                "doctor_schedule_id": selected_schedule.id,
                "doctor_id": result.doctor_id,
                "dept_sub_id": result.dept_sub_id,
                "appointment_date": result.date,
                "slot": selected_schedule.slot,
                "doctor_name": result.doctor_name,
                "schedule_options": [
                    {
                        "doctor_schedule_id": schedule.id,
                        "slot": schedule.slot,
                    }
                    for schedule in result.schedules
                ],
            }
        },
    )


def _normalize_schedule_item(
    item: dict,
    *,
    dept_sub_id: int | None,
    appointment_date: str | None,
) -> dict:
    normalized = dict(item)
    if dept_sub_id is not None:
        normalized.setdefault("deptSubId", dept_sub_id)
        normalized.setdefault("dept_sub_id", dept_sub_id)
    if appointment_date:
        normalized.setdefault("date", appointment_date)
        normalized.setdefault("appointment_date", appointment_date)
    return normalized


async def _save_schedule_candidates(schedule_items: list[dict]) -> None:
    thread_key = _build_flow_state_key()
    if thread_key is None or not schedule_items:
        return

    store = get_flow_state_store()
    flow_state = await store.load(thread_key)
    candidates = dict(flow_state.schedule_candidates_by_work_plan or {})

    for item in schedule_items:
        work_plan_id = item.get("workPlanId", item.get("work_plan_id"))
        if not work_plan_id:
            continue
        candidates[int(work_plan_id)] = {
            "doctor_id": item.get("doctorId", item.get("doctor_id")),
            "doctor_name": item.get("doctorName", item.get("doctor_name")),
            "dept_sub_id": item.get("deptSubId", item.get("dept_sub_id")),
            "appointment_date": item.get("date", item.get("appointment_date")),
        }

    flow_state.schedule_candidates_by_work_plan = candidates
    await store.save(thread_key, flow_state)


async def _hydrate_schedule_detail(result):
    thread_key = _build_flow_state_key()
    if thread_key is None:
        return result

    flow_state = await get_flow_state_store().load(thread_key)
    candidates = flow_state.schedule_candidates_by_work_plan or {}
    candidate = candidates.get(int(result.work_plan_id))
    if not candidate:
        return result

    updates = {}
    if result.dept_sub_id is None:
        updates["dept_sub_id"] = candidate.get("dept_sub_id")
    if result.date is None:
        updates["date"] = candidate.get("appointment_date")
    if result.doctor_id is None:
        updates["doctor_id"] = candidate.get("doctor_id")
    if not result.doctor_name:
        updates["doctor_name"] = candidate.get("doctor_name")

    if not updates:
        return result

    return result.model_copy(update=updates)


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
        effective_date = date or date_type.today().isoformat()
        try:
            if sub_dept_ids and doctor_id is None:
                for sid in sub_dept_ids:
                    resp = await hms_client.doctor_service.schedules(
                        ScheduleListRequest(dept_sub_id=sid, date=effective_date)
                    )
                    all_schedules.extend(
                        [
                            _normalize_schedule_item(
                                item,
                                dept_sub_id=sid,
                                appointment_date=effective_date,
                            )
                            for item in resp.items
                        ]
                    )
            else:
                current_sub_dept_id = sub_dept_ids[0] if sub_dept_ids else None
                resp = await hms_client.doctor_service.schedules(
                    ScheduleListRequest(
                        dept_sub_id=current_sub_dept_id,
                        date=effective_date,
                        doctor_id=doctor_id,
                    )
                )
                all_schedules.extend(
                    [
                        _normalize_schedule_item(
                            item,
                            dept_sub_id=current_sub_dept_id,
                            appointment_date=effective_date,
                        )
                        for item in resp.items
                    ]
                )
        except Exception as e:
            logger.error(f"query_doctor_schedules 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )

        if not all_schedules:
            return empty("近期无排班数据")

        await _save_schedule_candidates(all_schedules)
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

        result = await _hydrate_schedule_detail(result)
        await _save_pending_registration_confirmation(result)
        return ok("排班详情", result.model_dump())

    return [query_doctors, query_doctor_schedules, query_schedule_detail]
