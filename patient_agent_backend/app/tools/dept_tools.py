"""科室查询工具"""

from langchain_core.tools import tool

from app.hms_client import HmsClient
from app.hms_client.models import DeptDetailRequest, DeptListRequest


def create_dept_tools(hms_client: HmsClient):
    """创建科室相关工具（闭包注入 hms_client）"""

    @tool
    async def query_departments(page: int = 1, page_size: int = 20) -> str:
        """查询医院所有科室列表，包含科室名称、楼层位置和简介。
        当患者询问"有哪些科室""XX科在几楼"时使用此工具。"""
        result = await hms_client.dept_service.list_depts(
            DeptListRequest(page=page, page_size=page_size)
        )
        return result.model_dump_json()

    @tool
    async def query_dept_detail(dept_id: int) -> str:
        """查询科室详情及该科室下的诊室列表。
        当患者想了解某个科室的详细信息或该科室有哪些诊室时使用此工具。"""
        result = await hms_client.dept_service.detail(
            DeptDetailRequest(id=dept_id)
        )
        return result.model_dump_json()

    return [query_departments, query_dept_detail]
