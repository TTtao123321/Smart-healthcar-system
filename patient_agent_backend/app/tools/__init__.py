"""工具层 — 统一导出所有工具"""

from app.hms_client import HmsClient
from app.tools.dept_tools import create_dept_tools
from app.tools.doctor_tools import create_doctor_tools
from app.tools.registration_tools import create_registration_tools

# 全局工具列表（在应用启动时初始化）
ALL_TOOLS: list = []


def init_tools(hms_client: HmsClient) -> list:
    """初始化所有工具，注入 HMS 客户端"""
    tools = (
        create_dept_tools(hms_client)
        + create_doctor_tools(hms_client)
        + create_registration_tools(hms_client)
    )
    ALL_TOOLS.clear()
    ALL_TOOLS.extend(tools)
    return ALL_TOOLS
