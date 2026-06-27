"""请求上下文 — 跨工具调用传递会话信息（如 patient_id）"""

from contextvars import ContextVar

from app.auth.models import PatientSession

current_patient_session: ContextVar[PatientSession | None] = ContextVar(
    "current_patient_session", default=None
)
current_thread_id: ContextVar[str | None] = ContextVar("current_thread_id", default=None)


def set_patient_session(session: PatientSession | None) -> None:
    """设置当前请求的患者会话"""
    current_patient_session.set(session)


def get_patient_session() -> PatientSession | None:
    """获取当前请求的患者会话"""
    return current_patient_session.get()


def get_patient_id() -> int | None:
    """获取当前请求的真实患者 ID"""
    session = get_patient_session()
    if session is None:
        return None
    return session.patient_id


def set_thread_id(thread_id: str | None) -> None:
    """设置当前请求的线程 ID"""
    current_thread_id.set(thread_id)


def get_thread_id() -> str | None:
    """获取当前请求的线程 ID"""
    return current_thread_id.get()
