"""Shared runtime helpers for model-driven tool execution."""

import json
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.logging_utils import get_request_logger

logger = get_request_logger(__name__)

MAX_TOOL_ROUNDS = 5
TOOL_FOLLOWUP_PROMPT = (
    "【重要提醒】请基于以上工具返回的真实数据继续处理用户请求。"
    "如果当前信息仍不足以完成用户目标，请继续调用下一个必要工具；"
    "如果信息已经足够，请直接生成最终回复。"
    "若工具返回结果为空或查询失败，你必须如实告知用户'暂时无法获取该信息，请稍后再试'。"
    "严禁编造任何科室名称、医生姓名、职称、地址等医院信息。"
)


def recover_tool_call(user_content: str) -> dict[str, Any] | None:
    """Recover a tool call when the model emits an empty tool name."""
    text = (user_content or "").strip()
    if not text:
        return None

    if any(keyword in text for keyword in ("有哪些科室", "科室列表")):
        return {"name": "query_departments", "args": {}}

    if any(keyword in text for keyword in ("我的挂号", "我挂的号", "挂号记录", "看看我挂的")):
        return {"name": "query_registration", "args": {}}

    if any(keyword in text for keyword in ("哪些医生", "找医生", "出诊")):
        dept_match = re.search(r"([\u4e00-\u9fa5]{1,12}科)", text)
        if dept_match:
            return {
                "name": "query_doctors",
                "args": {"dept_name": dept_match.group(1)},
            }
        return {"name": "query_doctors", "args": {}}

    return None


def normalize_tool_calls(tool_calls: list[dict], last_user_content: str) -> list[dict]:
    normalized = []
    for tool_call in tool_calls:
        if tool_call.get("name"):
            normalized.append(tool_call)
            continue

        recovered = recover_tool_call(last_user_content)
        if recovered:
            fixed_tool_call = {**tool_call, **recovered}
            logger.warning("空工具名已按关键词规则回退: %s", fixed_tool_call)
            normalized.append(fixed_tool_call)
        else:
            logger.warning("忽略空工具名的 tool_call: %s", tool_call)

    return normalized


def classify_tool_result(tool_result_str: str) -> str:
    try:
        parsed = json.loads(tool_result_str)
    except (json.JSONDecodeError, TypeError):
        if not tool_result_str or tool_result_str in ("[]", "{}", '""', "null", "None"):
            return "empty_result"
        return "ok"

    if not isinstance(parsed, dict):
        return "ok"
    if parsed.get("ok") is False:
        error_message = str(parsed.get("error") or "")
        if any(keyword in error_message for keyword in ("参数", "格式错误", "请先确认", "缺失")):
            return "validation_error"
        return "upstream_error"
    if parsed.get("data") in ([], {}, None):
        return "empty_result"
    return "ok"


async def run_tool_rounds(
    *,
    llm,
    llm_messages: list,
    response,
    tools: list,
    last_user_content: str,
):
    tool_rounds = 0
    tool_map = {tool.name: tool for tool in tools}

    while isinstance(response, AIMessage) and response.tool_calls:
        tool_rounds += 1
        if tool_rounds > MAX_TOOL_ROUNDS:
            logger.error("工具调用轮次超过上限: %s", MAX_TOOL_ROUNDS)
            return AIMessage(content="系统暂时无法处理该请求，请稍后再试。")

        normalized_tool_calls = normalize_tool_calls(response.tool_calls, last_user_content)
        if not normalized_tool_calls:
            return AIMessage(content="系统暂时无法处理该请求，请稍后再试。")

        for tool_call in normalized_tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if tool_name not in tool_map:
                llm_messages.append(
                    HumanMessage(
                        content=f"未知工具：{tool_name}，请告知用户暂时无法处理该请求。"
                    )
                )
                continue

            try:
                logger.info(
                    "tool_call_start",
                    extra={
                        "tool_name": tool_name,
                        "tool_status": "start",
                        "route_type": "graph_route",
                        "degraded": False,
                    },
                )
                tool_result = await tool_map[tool_name].ainvoke(tool_args)
                tool_result_str = str(tool_result)
                error_type = classify_tool_result(tool_result_str)
                if error_type == "empty_result":
                    tool_result_str = "查询结果为空，数据库中暂无相关数据"

                llm_messages.append(AIMessage(content="", tool_calls=[tool_call]))
                llm_messages.append(
                    HumanMessage(content=f"工具 {tool_name} 返回结果：\n{tool_result_str}")
                )
                logger.info(
                    "tool_call_end",
                    extra={
                        "tool_name": tool_name,
                        "tool_status": "success",
                        "route_type": "graph_route",
                        "error_type": error_type,
                        "degraded": error_type != "ok",
                    },
                )
            except Exception as exc:
                logger.error("工具 %s 执行失败: %s", tool_name, exc)
                logger.error(
                    "tool_call_end",
                    extra={
                        "tool_name": tool_name,
                        "tool_status": "error",
                        "route_type": "graph_route",
                        "error_type": "runtime_error",
                        "degraded": True,
                    },
                )
                llm_messages.append(
                    HumanMessage(
                        content=(
                            f"工具 {tool_name} 执行失败：{str(exc)}。"
                            "请告知用户系统暂时无法查询该信息，不要编造任何数据。"
                        )
                    )
                )

        llm_messages.append(HumanMessage(content=TOOL_FOLLOWUP_PROMPT))
        response = await llm.ainvoke(llm_messages)

    return response
