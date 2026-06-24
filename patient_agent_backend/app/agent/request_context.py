"""请求上下文 — 跨工具调用传递会话信息（如 patient_id）"""

from contextvars import ContextVar

# 当前请求的 patient_id（业务标识，即用户的就诊卡号）
current_patient_id: ContextVar[str | None] = ContextVar(
    "current_patient_id", default=None
)


def set_patient_id(patient_id: str | None) -> None:
    """设置当前请求的 patient_id"""
    current_patient_id.set(patient_id)


def get_patient_id() -> str | None:
    """获取当前请求的 patient_id"""
    return current_patient_id.get()
