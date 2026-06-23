"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import compile_graph, reset_graph
from app.api import auth as auth_module
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router, set_memory
from app.config.settings import settings
from app.hms_client import HmsClient
from app.memory.redis_memory import RedisMemory
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

    # 初始化对话记忆
    memory = RedisMemory()
    await memory.connect()
    app.state.memory = memory
    set_memory(memory)
    logger.info("对话记忆初始化完成")

    # 初始化认证模块 Redis
    auth_module.set_redis(redis_client)
    logger.info("认证模块初始化完成")

    logger.info("patient_agent_backend 启动完成")

    yield

    # 关闭
    logger.info("正在关闭 patient_agent_backend...")
    await hms_client.close()
    await memory.close()
    await redis_client.close()
    logger.info("patient_agent_backend 已关闭")


app = FastAPI(
    title="智慧医疗助手 Agent 后端",
    description="基于 LangGraph 的智能导诊 Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)


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
