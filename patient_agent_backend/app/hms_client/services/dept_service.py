"""科室服务 — 对接 HMS 科室相关 API"""

import logging
from typing import TYPE_CHECKING

from app.hms_client.models import (
    DeptDetailRequest,
    DeptDetailResponse,
    DeptItem,
    DeptListRequest,
    DeptListResponse,
    SubDeptItem,
)

if TYPE_CHECKING:
    from app.hms_client.client import HmsClient

logger = logging.getLogger(__name__)


class DeptService:
    """科室服务"""

    def __init__(self, client: "HmsClient"):
        self._client = client

    async def list_depts(self, request: DeptListRequest | None = None) -> DeptListResponse:
        """查询科室列表

        对接 HMS: GET /medical/dept/selectAllDeptNameAndId
        或 POST /medical/dept/selectConditionByPage
        """
        if request is None:
            request = DeptListRequest()

        # 使用分页查询接口
        data = await self._client.post(
            "/medical/dept/selectConditionByPage",
            json={
                "page": request.page,
                "length": request.page_size,
                **({"name": request.name} if request.name else {}),
            },
        )

        result = data.get("result", {})
        items = []
        for item in result.get("list", []):
            items.append(DeptItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
                outpatient=item.get("outpatient"),
                description=item.get("description"),
                recommended=item.get("recommended"),
            ))

        return DeptListResponse(
            total=result.get("totalCount", 0) if isinstance(result, dict) else len(items),
            items=items,
        )

    async def detail(self, request: DeptDetailRequest) -> DeptDetailResponse:
        """查询科室详情（含诊室列表）

        对接 HMS: POST /medical/dept/selectById + GET /medical/dept/sub/selectByDeptId
        """
        # 查询科室信息
        data = await self._client.post(
            "/medical/dept/selectById",
            json={"id": request.id},
        )

        dept_data = data  # CommonResult.ok(map) 直接返回 map 内容
        if "result" in dept_data:
            dept_data = dept_data["result"]

        # 查询诊室列表
        sub_data = await self._client.get(
            "/medical/dept/sub/selectByDeptId",
            params={"deptId": request.id},
        )

        sub_items = []
        sub_list = sub_data.get("list", [])
        for item in sub_list:
            sub_items.append(SubDeptItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
                dept_id=item.get("deptId", item.get("dept_id", 0)),
                location=item.get("location", ""),
            ))

        return DeptDetailResponse(
            id=dept_data.get("id", 0),
            name=dept_data.get("name", ""),
            outpatient=dept_data.get("outpatient"),
            description=dept_data.get("description"),
            recommended=dept_data.get("recommended"),
            sub_depts=sub_items,
        )

    async def list_all_names(self) -> list[DeptItem]:
        """获取所有科室名称和 ID

        对接 HMS: GET /medical/dept/selectAllDeptNameAndId
        """
        data = await self._client.get("/medical/dept/selectAllDeptNameAndId")
        items = []
        for item in data.get("result", []):
            items.append(DeptItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
            ))
        return items

    async def list_sub_depts(self, dept_id: int) -> list[SubDeptItem]:
        """根据科室查询诊室列表

        对接 HMS: GET /medical/dept/sub/selectByDeptId
        """
        data = await self._client.get(
            "/medical/dept/sub/selectByDeptId",
            params={"deptId": dept_id},
        )

        items = []
        for item in data.get("list", []):
            items.append(SubDeptItem(
                id=item.get("id", 0),
                name=item.get("name", ""),
                dept_id=item.get("deptId", item.get("dept_id", dept_id)),
                location=item.get("location", ""),
            ))
        return items
