"""聊天接口（普通 + SSE 流式）"""

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import compile_graph
from app.agent.state import AgentState
from app.memory.redis_memory import RedisMemory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["聊天"])

# 全局依赖（在 main.py 中注入）
_memory: RedisMemory | None = None


def set_memory(memory: RedisMemory) -> None:
    global _memory
    _memory = memory


def get_memory() -> RedisMemory:
    if _memory is None:
        raise HTTPException(status_code=500, detail="对话记忆未初始化")
    return _memory


@router.post("")
async def chat(request: Request):
    """发送消息，返回完整响应"""
    body = await request.json()
    user_message = body.get("message", "")
    patient_id = body.get("patient_id", "anonymous")
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 加载对话历史
    memory = get_memory()
    history = await memory.load_messages(patient_id, thread_id)

    # 构建消息列表
    messages = []
    for msg in history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    # 构建 Agent 状态
    state: AgentState = {
        "messages": messages,
        "patient_id": patient_id,
        "guardrail_result": None,
        "needs_handoff": False,
        "disclaimer_shown": False,
        "conversation_turn": len(history) // 2 + 1,
    }

    # 执行 Agent
    try:
        graph = compile_graph()
        result = await graph.ainvoke(state)
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="智能助手暂时无法响应，请稍后再试")

    # 提取最后一条 AI 消息
    response_content = ""
    result_messages = result.get("messages", [])
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage) and msg.content:
            response_content = msg.content
            break

    # 保存对话历史
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response_content})
    await memory.save_messages(patient_id, thread_id, history)

    return {
        "message": response_content,
        "thread_id": thread_id,
        "needs_handoff": result.get("needs_handoff", False),
    }


@router.post("/stream")
async def chat_stream(request: Request):
    """发送消息，SSE 流式返回"""
    body = await request.json()
    user_message = body.get("message", "")
    patient_id = body.get("patient_id", "anonymous")
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    async def event_generator() -> AsyncGenerator[dict, None]:
        memory = get_memory()
        history = await memory.load_messages(patient_id, thread_id)

        messages = []
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_message))

        state: AgentState = {
            "messages": messages,
            "patient_id": patient_id,
            "guardrail_result": None,
            "needs_handoff": False,
            "disclaimer_shown": False,
            "conversation_turn": len(history) // 2 + 1,
        }

        try:
            graph = compile_graph()
            # 流式执行
            full_response = ""
            async for event in graph.astream_events(state, version="v2"):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {"content": chunk.content, "thread_id": thread_id},
                                ensure_ascii=False,
                            ),
                        }

            # 保存对话历史
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": full_response})
            await memory.save_messages(patient_id, thread_id, history)

            yield {
                "event": "done",
                "data": json.dumps({"thread_id": thread_id}, ensure_ascii=False),
            }

        except Exception as e:
            logger.error(f"Agent 流式执行失败: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": "智能助手暂时无法响应"}, ensure_ascii=False
                ),
            }

    return EventSourceResponse(event_generator())


@router.get("/history")
async def chat_history(
    patient_id: str = "anonymous",
    thread_id: str = "",
):
    """获取对话历史"""
    if not thread_id:
        return {"messages": []}

    memory = get_memory()
    messages = await memory.load_messages(patient_id, thread_id)
    return {"messages": messages, "thread_id": thread_id}
