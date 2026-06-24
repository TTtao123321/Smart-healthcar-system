"""科室查询工具"""

import logging

from langchain_core.tools import tool

from app.hms_client import HmsClient
from app.hms_client.models import DeptDetailRequest, DeptListRequest
from app.tools.name_resolver import resolve_dept
from app.tools.tool_response import empty, err, ok

logger = logging.getLogger(__name__)


def create_dept_tools(hms_client: HmsClient):
    """创建科室相关工具（闭包注入 hms_client）"""

    @tool
    async def query_departments() -> str:
        """查询医院所有科室列表（包含科室名称、楼层、简介）。
        当患者询问"有哪些科室""科室列表"时使用此工具。
        无需参数。

        返回格式：{"ok": true, "summary": "...", "data": [{"id": int, "name": str, ...}]}
        """
        try:
            result = await hms_client.dept_service.list_depts(
                DeptListRequest(page=1, page_size=50)
            )
        except Exception as e:
            logger.error(f"query_departments 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询科室信息，请稍后再试。",
            )

        if not result.items:
            return empty("未查询到任何科室")

        data = [d.model_dump() for d in result.items]
        return ok(f"共找到 {len(data)} 个科室", data)

    @tool
    async def query_dept_detail(dept_name: str) -> str:
        """查询某个科室的详情，包括该科室下的诊室列表（含楼层位置）。
        当患者询问"内科有哪些诊室""XX科在几楼"时使用此工具。

        dept_name: 科室名称（支持模糊匹配，如"内科"会匹配所有含"内科"的科室）

        返回格式：{"ok": true, "summary": "...", "data": {...}}
        """
        if not dept_name or not dept_name.strip():
            return err("参数 dept_name 不能为空", "请告知用户需要提供科室名称。")

        resolve_result = await resolve_dept(hms_client, dept_name)
        if resolve_result.error:
            return err(
                f"查询科室失败: {resolve_result.error}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )
        if not resolve_result.found:
            return empty(f"未找到名称包含「{dept_name}」的科室")

        # 如果匹配到多个，返回列表让 LLM 引导用户选择
        if len(resolve_result.items) > 1:
            data = [d.model_dump() for d in resolve_result.items]
            return ok(
                f"匹配到 {len(data)} 个科室，请引导用户选择具体科室",
                data,
            )

        # 唯一匹配 → 查详情
        dept = resolve_result.items[0]
        try:
            detail = await hms_client.dept_service.detail(
                DeptDetailRequest(id=dept.id)
            )
        except Exception as e:
            logger.error(f"query_dept_detail 调用 HMS 失败: {e}")
            return err(
                f"HMS 服务调用失败: {e}",
                "请告知用户系统暂时无法查询，请稍后再试。",
            )

        return ok(f"科室「{detail.name}」详情", detail.model_dump())

    return [query_departments, query_dept_detail]
