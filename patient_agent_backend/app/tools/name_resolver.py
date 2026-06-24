"""名称解析辅助：将科室/医生中文名模糊匹配为 HMS ID"""

import logging
from dataclasses import dataclass

from app.hms_client import HmsClient
from app.hms_client.models import (
    DeptDetailRequest,
    DeptListRequest,
    DoctorListRequest,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolveResult:
    """解析结果"""

    found: bool  # 是否找到匹配
    items: list  # 所有匹配项
    error: str = ""  # 失败原因（HMS 异常时）


async def resolve_dept(hms_client: HmsClient, dept_name: str) -> ResolveResult:
    """根据科室名模糊匹配科室。

    返回所有名称包含 dept_name 的 DeptItem 列表。
    """
    try:
        result = await hms_client.dept_service.list_depts(
            DeptListRequest(page=1, page_size=100)
        )
    except Exception as e:
        logger.error(f"resolve_dept 调用 HMS 失败: {e}")
        return ResolveResult(found=False, items=[], error=str(e))

    keyword = dept_name.strip()
    matched = [d for d in result.items if keyword in (d.name or "")]
    return ResolveResult(found=len(matched) > 0, items=matched)


async def resolve_sub_dept(
    hms_client: HmsClient, dept_name: str
) -> ResolveResult:
    """根据科室名模糊匹配诊室（sub_dept），用于查医生/排班所需的 dept_sub_id。

    优先策略：找到匹配的科室 → 取该科室下所有诊室。
    """
    dept_result = await resolve_dept(hms_client, dept_name)
    if dept_result.error:
        return dept_result
    if not dept_result.found:
        return ResolveResult(found=False, items=[])

    sub_depts = []
    for dept in dept_result.items:
        try:
            detail = await hms_client.dept_service.detail(
                DeptDetailRequest(id=dept.id)
            )
            if detail.sub_depts:
                sub_depts.extend(detail.sub_depts)
        except Exception as e:
            logger.warning(f"resolve_sub_dept 查询科室详情失败 id={dept.id}: {e}")
            continue

    return ResolveResult(found=len(sub_depts) > 0, items=sub_depts)


async def resolve_doctor(
    hms_client: HmsClient,
    doctor_name: str | None = None,
    dept_name: str | None = None,
) -> ResolveResult:
    """根据医生名/科室名解析医生列表。

    - 仅 doctor_name：在全部医生中按姓名模糊匹配
    - 仅 dept_name：返回该科室下所有医生（先解析诊室再查）
    - 同时给：先按科室筛诊室，再在每个诊室下查含 doctor_name 的医生
    """
    if not doctor_name and not dept_name:
        return ResolveResult(found=False, items=[], error="未提供姓名或科室")

    # 解析诊室 ID 列表
    sub_dept_ids: list[int] = []
    if dept_name:
        sub_result = await resolve_sub_dept(hms_client, dept_name)
        if sub_result.error:
            return ResolveResult(found=False, items=[], error=sub_result.error)
        if not sub_result.found:
            return ResolveResult(found=False, items=[])
        sub_dept_ids = [s.id for s in sub_result.items]

    keyword = (doctor_name or "").strip()
    all_doctors: list = []

    try:
        if sub_dept_ids:
            for sid in sub_dept_ids:
                resp = await hms_client.doctor_service.list_doctors(
                    DoctorListRequest(
                        name=keyword if keyword else None,
                        dept_sub_id=sid,
                        page=1,
                        page_size=50,
                    )
                )
                all_doctors.extend(resp.items)
        else:
            resp = await hms_client.doctor_service.list_doctors(
                DoctorListRequest(name=keyword, page=1, page_size=50)
            )
            all_doctors.extend(resp.items)
    except Exception as e:
        logger.error(f"resolve_doctor 查询医生失败: {e}")
        return ResolveResult(found=False, items=[], error=str(e))

    # 当未指定诊室且 HMS 的 name 模糊匹配可能不准，这里再补一层 contains 过滤
    if keyword and not sub_dept_ids:
        all_doctors = [d for d in all_doctors if keyword in (d.name or "")]

    # 去重（按 id）
    seen = set()
    unique = []
    for d in all_doctors:
        if d.id not in seen:
            seen.add(d.id)
            unique.append(d)

    return ResolveResult(found=len(unique) > 0, items=unique)
