"""患者认证接口"""

import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_patient_session
from app.auth.models import PatientSession
from app.auth.service import AuthService
from app.config.settings import settings
from app.e2e.service import get_e2e_service
from app.hms_client.models import (
    PatientLoginRequest,
    PatientLoginResponse,
    SmsCodeRequest,
    SmsCodeResponse,
)
from app.patient_profile.service import PatientProfileService
from app.patient_sidebar.service import PatientSidebarService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["认证"])

_redis: aioredis.Redis | None = None
_SMS_PREFIX = "sms:code:"
_SMS_TTL = 300  # 5 分钟
_patient_profile_service_getter = None
_auth_service_getter = None
_patient_sidebar_service_getter = None


def set_redis(redis: aioredis.Redis) -> None:
    global _redis
    _redis = redis


def _get_redis() -> aioredis.Redis:
    if _redis is None:
        raise HTTPException(status_code=500, detail="Redis 未初始化")
    return _redis


def set_patient_profile_service_getter(getter) -> None:
    global _patient_profile_service_getter
    _patient_profile_service_getter = getter


def get_patient_profile_service() -> PatientProfileService:
    if _patient_profile_service_getter is None:
        raise HTTPException(status_code=500, detail="患者档案服务未初始化")
    return _patient_profile_service_getter()


def set_auth_service_getter(getter) -> None:
    global _auth_service_getter
    _auth_service_getter = getter


def get_auth_service() -> AuthService:
    if _auth_service_getter is None:
        return AuthService(_get_redis())
    return _auth_service_getter()


def set_patient_sidebar_service_getter(getter) -> None:
    global _patient_sidebar_service_getter
    _patient_sidebar_service_getter = getter


def get_patient_sidebar_service() -> PatientSidebarService:
    if _patient_sidebar_service_getter is None:
        raise HTTPException(status_code=500, detail="患者侧栏服务未初始化")
    return _patient_sidebar_service_getter()


@router.post("/send-sms", response_model=SmsCodeResponse)
async def send_sms_code(request: SmsCodeRequest):
    """发送短信验证码（开发模式直接返回验证码）"""
    if settings.patient_agent_e2e_mode:
        return SmsCodeResponse(
            msg="验证码已发送",
            code_dev=get_e2e_service().get_sms_code(request.phone),
        )

    import random

    r = _get_redis()
    code = f"{random.randint(100000, 999999)}"
    key = f"{_SMS_PREFIX}{request.phone}"

    await r.set(key, code, ex=_SMS_TTL)

    # 开发模式：日志打印验证码
    logger.info(f"【开发模式】手机号 {request.phone} 验证码: {code}")

    return SmsCodeResponse(msg="验证码已发送", code_dev=code)


@router.post("/login", response_model=PatientLoginResponse)
async def login(request: PatientLoginRequest):
    """患者登录（验证码登录）"""
    if settings.patient_agent_e2e_mode:
        if request.code != settings.patient_agent_e2e_code:
            raise HTTPException(status_code=400, detail="验证码错误")
        session = await get_e2e_service().create_session(
            phone=request.phone,
            name=settings.patient_agent_e2e_patient_name,
            patient_id=settings.patient_agent_e2e_patient_id,
        )
        return PatientLoginResponse(
            token=session.token,
            patient_id=session.patient_id,
            name=session.name,
        )

    r = _get_redis()
    key = f"{_SMS_PREFIX}{request.phone}"

    saved_code = await r.get(key)
    if saved_code is None:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if saved_code != request.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证通过，删除验证码
    await r.delete(key)

    profile = await get_patient_profile_service().get_or_create_by_phone(request.phone)
    session = await get_auth_service().create_session(
        phone=request.phone,
        name=profile.name,
        patient_id=profile.id,
    )

    return PatientLoginResponse(
        token=session.token,
        patient_id=session.patient_id,
        name=session.name,
    )


@router.post("/logout")
async def logout(session: PatientSession = Depends(require_patient_session)):
    """患者登出"""
    await get_auth_service().logout(session.token)
    return {"msg": "登出成功"}
