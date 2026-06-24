"""LangGraph 图节点实现"""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.prompts import HANDOFF_MESSAGE, SYSTEM_PROMPT
from app.agent.state import AgentState
from app.config.settings import settings
from app.guardrails.input_guard import check_input
from app.guardrails.output_guard import check_output

logger = logging.getLogger(__name__)

# 复用 LLM 实例（避免每次请求重新创建）
_llm: ChatOpenAI | None = None
_llm_with_tools: ChatOpenAI | None = None


def _get_llm(tools: list | None = None) -> ChatOpenAI:
    """获取 LLM 实例（带缓存）"""
    global _llm, _llm_with_tools

    if tools:
        if _llm_with_tools is None:
            base_llm = _get_llm()
            _llm_with_tools = base_llm.bind_tools(tools)
        return _llm_with_tools

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
    _llm_with_tools = None


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


async def agent(state: AgentState, tools: list) -> dict:
    """LLM 推理节点 — 内部处理工具调用循环"""
    messages = state.get("messages", [])

    # 如果护栏已拦截，不再调用 LLM
    guardrail_result = state.get("guardrail_result", "")
    if guardrail_result in ("diagnosis_request", "report_interpretation", "high_emergency"):
        return {}

    # 构建消息列表，添加 SystemMessage
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    llm_messages = [system_msg] + list(messages)

    # 获取 LLM 实例（绑定工具）
    llm = _get_llm(tools if tools else None)

    # 异步调用 LLM
    response = await llm.ainvoke(llm_messages)

    # 如果 LLM 调用了工具，执行工具并将结果作为上下文再次调用 LLM
    if isinstance(response, AIMessage) and response.tool_calls:
        # 构建工具名称到函数的映射
        tool_map = {t.name: t for t in tools}
        has_empty_result = False

        # 执行工具调用
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if not tool_name:
                logger.warning(f"忽略空工具名的 tool_call: {tool_call}")
                continue
            if tool_name in tool_map:
                try:
                    tool_result = await tool_map[tool_name].ainvoke(tool_args)
                    # 检查工具返回是否为空
                    tool_result_str = str(tool_result)
                    if not tool_result_str or tool_result_str in ("[]", "{}", '""', "null", "None"):
                        has_empty_result = True
                        tool_result_str = "查询结果为空，数据库中暂无相关数据"
                    # 将工具结果作为 HumanMessage 添加到消息列表
                    llm_messages.append(AIMessage(
                        content="",
                        tool_calls=[tool_call],
                    ))
                    llm_messages.append(HumanMessage(
                        content=f"工具 {tool_name} 返回结果：\n{tool_result_str}"
                    ))
                except Exception as e:
                    logger.error(f"工具 {tool_name} 执行失败: {e}")
                    has_empty_result = True
                    llm_messages.append(HumanMessage(
                        content=f"工具 {tool_name} 执行失败：{str(e)}。请告知用户系统暂时无法查询该信息，不要编造任何数据。"
                    ))
            else:
                llm_messages.append(HumanMessage(
                    content=f"未知工具：{tool_name}，请告知用户暂时无法处理该请求。"
                ))

        # 添加数据真实性提醒
        llm_messages.append(HumanMessage(
            content=(
                "【重要提醒】请基于以上工具返回的真实数据生成回复。"
                "如果工具返回结果为空或查询失败，你必须如实告知用户'暂时无法获取该信息，请稍后再试'。"
                "严禁编造任何科室名称、医生姓名、职称、地址等医院信息。"
            )
        ))

        # 再次调用 LLM（不带工具），生成最终回复
        llm_no_tools = _get_llm()
        response = await llm_no_tools.ainvoke(llm_messages)

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
