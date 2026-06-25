from fastapi import Header, HTTPException

from app.auth.models import PatientSession


_auth_service_getter = None


def set_auth_service_getter(getter):
    global _auth_service_getter
    _auth_service_getter = getter


def get_auth_service():
    if _auth_service_getter is None:
        raise HTTPException(status_code=500, detail="认证服务未初始化")
    return _auth_service_getter()


async def require_patient_session(authorization: str | None = Header(default=None)) -> PatientSession:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    session = await get_auth_service().get_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session
