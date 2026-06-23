"""患者认证接口 — 自实现验证码登录"""

import logging
import uuid
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException

from app.hms_client.models import (
    PatientLoginRequest,
    PatientLoginResponse,
    SmsCodeRequest,
    SmsCodeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["认证"])

_redis: aioredis.Redis | None = None
_SMS_PREFIX = "sms:code:"
_SMS_TTL = 300  # 5 分钟


def set_redis(redis: aioredis.Redis) -> None:
    global _redis
    _redis = redis


def _get_redis() -> aioredis.Redis:
    if _redis is None:
        raise HTTPException(status_code=500, detail="Redis 未初始化")
    return _redis


@router.post("/send-sms", response_model=SmsCodeResponse)
async def send_sms_code(request: SmsCodeRequest):
    """发送短信验证码（开发模式直接返回验证码）"""
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
    r = _get_redis()
    key = f"{_SMS_PREFIX}{request.phone}"

    saved_code = await r.get(key)
    if saved_code is None:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if saved_code != request.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证通过，删除验证码
    await r.delete(key)

    # 生成 token（MVP 阶段使用简单 UUID）
    token = str(uuid.uuid4())

    # 缓存患者信息到 Redis
    patient_key = f"patient:token:{token}"
    await r.hset(patient_key, mapping={
        "phone": request.phone,
        "name": f"患者{request.phone[-4:]}",
        "login_time": datetime.now().isoformat(),
    })
    await r.expire(patient_key, 86400 * 7)  # 7 天过期

    return PatientLoginResponse(
        token=token,
        patient_id=0,  # MVP 阶段暂不关联 HMS 患者ID
        name=f"患者{request.phone[-4:]}",
    )


@router.post("/logout")
async def logout():
    """患者登出"""
    return {"msg": "登出成功"}
