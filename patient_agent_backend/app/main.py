"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

import aiomysql
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import compile_graph, reset_graph
from app.auth.dependencies import set_auth_service_getter as set_auth_dependency_getter
from app.auth.service import AuthService
from app.api import auth as auth_module
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router, set_memory
from app.api.patient import router as patient_router
from app.config.settings import settings
from app.hms_client import HmsClient
from app.memory.redis_memory import RedisMemory
from app.middleware.request_context import RequestContextMiddleware
from app.patient_profile.repository import PatientProfileRepository
from app.patient_profile.service import PatientProfileService
from app.patient_sidebar.schedule_gateway import PatientScheduleGateway
from app.patient_sidebar.service import PatientSidebarService
from app.tools import init_tools

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("正在初始化 patient_agent_backend...")

    # 初始化 HMS 客户端
    hms_client = HmsClient()
    app.state.hms_client = hms_client

    # 登录 HMS 管理端（获取 SaToken）
    await hms_client.login_admin()

    # 初始化工具
    init_tools(hms_client)
    reset_graph()  # 重置图缓存
    logger.info("工具初始化完成")

    # 预编译 Agent 图
    compile_graph()
    logger.info("Agent 图编译完成")

    # 初始化 Redis
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    # 初始化 HMS MySQL
    mysql_pool = await aiomysql.create_pool(
        host=settings.hms_db_host,
        port=settings.hms_db_port,
        user=settings.hms_db_user,
        password=settings.hms_db_password,
        db=settings.hms_db_name,
        autocommit=True,
    )
    app.state.mysql_pool = mysql_pool

    patient_profile_repository = PatientProfileRepository(mysql_pool)
    patient_profile_service = PatientProfileService(patient_profile_repository)
    auth_service = AuthService(redis_client)
    patient_sidebar_service = PatientSidebarService(
        profile_service=patient_profile_service,
        registration_service=hms_client.registration_service,
        schedule_gateway=PatientScheduleGateway(
            dept_service=hms_client.dept_service,
            doctor_service=hms_client.doctor_service,
        ),
    )
    app.state.patient_profile_service = patient_profile_service
    app.state.auth_service = auth_service
    app.state.patient_sidebar_service = patient_sidebar_service

    # 初始化对话记忆
    memory = RedisMemory()
    await memory.connect()
    app.state.memory = memory
    set_memory(memory)
    logger.info("对话记忆初始化完成")

    # 初始化认证模块 Redis
    auth_module.set_redis(redis_client)
    auth_module.set_patient_profile_service_getter(lambda: app.state.patient_profile_service)
    auth_module.set_auth_service_getter(lambda: app.state.auth_service)
    auth_module.set_patient_sidebar_service_getter(lambda: app.state.patient_sidebar_service)
    set_auth_dependency_getter(lambda: app.state.auth_service)
    logger.info("认证模块初始化完成")

    logger.info("patient_agent_backend 启动完成")

    yield

    # 关闭
    logger.info("正在关闭 patient_agent_backend...")
    await hms_client.close()
    await memory.close()
    mysql_pool.close()
    await mysql_pool.wait_closed()
    await redis_client.close()
    logger.info("patient_agent_backend 已关闭")


app = FastAPI(
    title="智慧医疗助手 Agent 后端",
    description="基于 LangGraph 的智能导诊 Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(patient_router)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
