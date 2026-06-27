"""聊天接口（普通 + SSE 流式）"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import compile_graph
from app.auth.dependencies import require_patient_session
from app.auth.models import PatientSession
from app.chat.orchestrator import ChatOrchestrator
from app.memory.redis_memory import RedisMemory

router = APIRouter(prefix="/api/chat", tags=["聊天"])

# 全局依赖（在 main.py 中注入）
_memory: RedisMemory | None = None
_orchestrator: ChatOrchestrator | None = None


def set_memory(memory: RedisMemory) -> None:
    global _memory, _orchestrator
    _memory = memory
    _orchestrator = None


def get_memory() -> RedisMemory:
    if _memory is None:
        raise HTTPException(status_code=500, detail="对话记忆未初始化")
    return _memory


def get_orchestrator() -> ChatOrchestrator:
    if _orchestrator is None:
        memory = get_memory()
        return ChatOrchestrator(memory=memory, graph_factory=compile_graph)
    return _orchestrator


@router.post("")
async def chat(request: Request, session: PatientSession = Depends(require_patient_session)):
    """发送消息，返回完整响应"""
    body = await request.json()
    user_message = body.get("message", "")
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    result = await get_orchestrator().run_once(
        session=session,
        user_message=user_message,
        thread_id=thread_id,
    )

    return {
        "message": result.message,
        "thread_id": result.thread_id,
        "needs_handoff": result.needs_handoff,
        "reply_type": result.reply_type,
        "degraded": result.degraded,
    }


@router.post("/stream")
async def chat_stream(request: Request, session: PatientSession = Depends(require_patient_session)):
    """发送消息，SSE 流式返回"""
    body = await request.json()
    user_message = body.get("message", "")
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    async def event_generator():
        async for event in get_orchestrator().run_stream(
            session=session,
            user_message=user_message,
            thread_id=thread_id,
        ):
            event_name = event.event if hasattr(event, "event") else event.get("event", "message")
            event_data = event.data if hasattr(event, "data") else event.get("data", {})
            yield {
                "event": event_name,
                "data": json.dumps(event_data, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


@router.get("/history")
async def chat_history(
    thread_id: str = "",
    session: PatientSession = Depends(require_patient_session),
):
    """获取对话历史"""
    if not thread_id:
        return {"messages": []}

    memory = get_memory()
    messages = await memory.load_messages(session.patient_id, thread_id)
    return {"messages": messages, "thread_id": thread_id}


@router.get("/threads")
async def chat_threads(
    session: PatientSession = Depends(require_patient_session),
):
    """获取当前患者的历史会话列表"""
    memory = get_memory()
    threads = await memory.list_threads(session.patient_id)
    return {"threads": threads}


@router.delete("/threads/{thread_id}")
async def delete_chat_thread(
    thread_id: str,
    session: PatientSession = Depends(require_patient_session),
):
    """删除当前患者的历史会话"""
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    memory = get_memory()
    await memory.delete_thread(session.patient_id, thread_id)
    return {"ok": True}
