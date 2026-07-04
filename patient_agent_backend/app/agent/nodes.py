"""LangGraph 图节点实现"""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.tool_runtime import recover_tool_call, run_tool_rounds
from app.logging_utils import get_request_logger
from app.agent.prompts import HANDOFF_MESSAGE, SYSTEM_PROMPT
from app.agent.state import AgentState
from app.config.settings import settings
from app.guardrails.input_guard import check_input
from app.guardrails.output_guard import check_output

logger = get_request_logger(__name__)

# 复用 LLM 实例（避免每次请求重新创建）
_llm: ChatOpenAI | None = None
_llm_with_tools: dict[tuple[str, ...], ChatOpenAI] = {}


def _get_llm(tools: list | None = None) -> ChatOpenAI:
    """获取 LLM 实例（带缓存）"""
    global _llm, _llm_with_tools

    if tools:
        tool_key = tuple(tool.name for tool in tools)
        if tool_key not in _llm_with_tools:
            base_llm = _get_llm()
            _llm_with_tools[tool_key] = base_llm.bind_tools(tools)
        return _llm_with_tools[tool_key]

    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.0,
        )
    return _llm


def reset_llm() -> None:
    """重置 LLM 缓存（配置变更后调用）"""
    global _llm, _llm_with_tools
    _llm = None
    _llm_with_tools = {}

def guard_in(state: AgentState) -> dict:
    """输入安全护栏节点"""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {}

    user_content = last_message.content
    result = check_input(user_content)

    updates: dict[str, Any] = {
        "guardrail_result": result.reason,
        "needs_handoff": result.needs_handoff,
    }

    if result.blocked:
        # 拦截：添加护栏 AI 响应到消息链
        updates["messages"] = [AIMessage(content=result.response)]
    elif result.needs_disclaimer:
        updates["disclaimer_shown"] = state.get("disclaimer_shown", False)

    return updates


async def agent(state: AgentState, tools: list, system_prompt: str = SYSTEM_PROMPT) -> dict:
    """LLM 推理节点 — 内部处理工具调用循环"""
    messages = state.get("messages", [])

    # 如果护栏已拦截，不再调用 LLM
    guardrail_result = state.get("guardrail_result", "")
    if guardrail_result in ("diagnosis_request", "report_interpretation", "high_emergency"):
        return {}

    # 构建消息列表，添加 SystemMessage
    system_msg = SystemMessage(content=system_prompt)
    llm_messages = [system_msg] + list(messages)

    # 获取 LLM 实例（绑定工具）
    llm = _get_llm(tools if tools else None)

    # 异步调用 LLM
    response = await llm.ainvoke(llm_messages)
    last_user_content = ""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            last_user_content = str(message.content)
            break

    response = await run_tool_rounds(
        llm=llm,
        llm_messages=llm_messages,
        response=response,
        tools=tools,
        last_user_content=last_user_content,
    )

    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """路由函数 — 决定 agent 节点后的走向"""
    # 如果护栏拦截需要转人工，直接转人工
    if state.get("needs_handoff"):
        return "handoff"

    # 否则正常结束
    return "end"


def guard_out(state: AgentState) -> dict:
    """输出安全护栏节点"""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return {}

    needs_disclaimer = state.get("guardrail_result") == "health_topic"
    disclaimer_shown = state.get("disclaimer_shown", False)

    processed_content, new_disclaimer_shown = check_output(
        last_message.content,
        needs_disclaimer=needs_disclaimer,
        disclaimer_shown=disclaimer_shown,
    )

    updates: dict[str, Any] = {}
    if processed_content != last_message.content:
        # 替换最后一条消息
        new_message = AIMessage(content=processed_content)
        updates["messages"] = messages[:-1] + [new_message]
    updates["disclaimer_shown"] = new_disclaimer_shown

    return updates


def handoff(state: AgentState) -> dict:
    """转人工节点"""
    return {
        "messages": [AIMessage(content=HANDOFF_MESSAGE)],
    }
