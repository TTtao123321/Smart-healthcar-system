"""Deterministic pre-routing for high-confidence patient flows."""

import json
import re

from app.agent.tool_runtime import classify_tool_result
from app.chat.flow_state import get_flow_state_store
from app.chat.models import ChatRunResult
from app.logging_utils import get_request_logger

logger = get_request_logger(__name__)

QUERY_REGISTRATION_PATTERNS = ("我的挂号", "挂号记录", "我挂了哪些号", "我挂的号")
CANCEL_PATTERNS = ("取消挂号", "退号", "取消这个预约", "取消预约")
CONFIRM_PATTERNS = ("确认", "就这个", "帮我预约这个", "帮我挂这个")


def _find_tool(tool_name: str):
    from app.tools import ALL_TOOLS

    return next((tool for tool in ALL_TOOLS if tool.name == tool_name), None)


async def _invoke_tool(tool_name: str, args: dict) -> str:
    tool = _find_tool(tool_name)
    if tool is None:
        raise ValueError(f"tool not found: {tool_name}")
    return await tool.ainvoke(args)


def _parse_tool_result(tool_result: str) -> dict:
    try:
        parsed = json.loads(tool_result)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"ok": False, "error": "工具返回结果无法解析", "hint": "请稍后再试。"}


def _format_registration_items(items: list[dict]) -> str:
    lines = []
    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index}. 记录ID {item.get('id', '-')}"
            f"，就诊日期 {item.get('appointment_date') or '未知'}"
            f"，时段 {item.get('slot') if item.get('slot') is not None else '未知'}"
        )
    return "\n".join(lines)


def _format_tool_message(tool_name: str, tool_result: str) -> str:
    payload = _parse_tool_result(tool_result)
    if payload.get("ok") is False:
        return payload.get("hint") or payload.get("error") or "系统暂时无法处理该请求，请稍后再试。"

    data = payload.get("data")
    summary = payload.get("summary") or "操作已完成"
    if data in (None, [], {}):
        return payload.get("hint") or summary

    if tool_name == "query_registration" and isinstance(data, list):
        return f"{summary}：\n{_format_registration_items(data)}"

    if tool_name == "create_registration":
        registration_id = data.get("id") if isinstance(data, dict) else None
        if registration_id is not None:
            return f"{summary}，挂号记录ID {registration_id}。"
        return summary

    if tool_name == "cancel_registration":
        return summary

    return summary


def _pick_confirmation_slot(user_message: str, pending_confirmation: dict) -> int | None:
    slot_match = re.search(r"第\s*(\d+)\s*(?:个|时段)", user_message)
    if slot_match:
        return int(slot_match.group(1))

    direct_match = re.search(r"(?:选|第)\s*(\d+)", user_message)
    if direct_match:
        return int(direct_match.group(1))

    return pending_confirmation.get("slot")


def _log_pre_route(*, patient_id: int, thread_id: str, tool_name: str, tool_result: str) -> None:
    error_type = classify_tool_result(tool_result)
    logger.info(
        "pre_route_hit",
        extra={
            "patient_id": patient_id,
            "thread_id": thread_id,
            "tool_name": tool_name,
            "tool_status": "success",
            "route_type": "pre_route",
            "error_type": error_type,
            "degraded": error_type != "ok",
        },
    )


async def try_pre_route(*, session, thread_id: str, user_message: str) -> ChatRunResult | None:
    text = (user_message or "").strip()
    if not text:
        return None

    state = await get_flow_state_store().load(f"patient:{session.patient_id}:{thread_id}")

    if any(keyword in text for keyword in QUERY_REGISTRATION_PATTERNS):
        tool_result = await _invoke_tool("query_registration", {})
        _log_pre_route(
            patient_id=session.patient_id,
            thread_id=thread_id,
            tool_name="query_registration",
            tool_result=tool_result,
        )
        return ChatRunResult(
            thread_id=thread_id,
            message=_format_tool_message("query_registration", tool_result),
            reply_type="pre_route",
            needs_handoff=False,
            disclaimer_added=False,
            guardrail_result=None,
            degraded=False,
        )

    if any(keyword in text for keyword in CANCEL_PATTERNS):
        tool_result = await _invoke_tool("query_registration", {})
        _log_pre_route(
            patient_id=session.patient_id,
            thread_id=thread_id,
            tool_name="query_registration",
            tool_result=tool_result,
        )
        message = _format_tool_message("query_registration", tool_result)
        if "记录ID" in message:
            message = f"{message}\n请告诉我想取消哪一条挂号记录，直接回复记录ID即可。"
        return ChatRunResult(
            thread_id=thread_id,
            message=message,
            reply_type="pre_route",
            needs_handoff=False,
            disclaimer_added=False,
            guardrail_result=None,
            degraded=False,
        )

    pending_confirmation = state.pending_registration_confirmation or {}
    if pending_confirmation and (
        any(keyword in text for keyword in CONFIRM_PATTERNS)
        or re.search(r"第\s*\d+\s*(?:个|时段)", text)
    ):
        slot = _pick_confirmation_slot(text, pending_confirmation)
        if slot is None:
            return ChatRunResult(
                thread_id=thread_id,
                message="当前缺少可确认的时段信息，请重新选择医生和时段。",
                reply_type="pre_route",
                needs_handoff=False,
                disclaimer_added=False,
                guardrail_result=None,
                degraded=False,
            )

        tool_result = await _invoke_tool("create_registration", {"slot": slot})
        _log_pre_route(
            patient_id=session.patient_id,
            thread_id=thread_id,
            tool_name="create_registration",
            tool_result=tool_result,
        )
        return ChatRunResult(
            thread_id=thread_id,
            message=_format_tool_message("create_registration", tool_result),
            reply_type="pre_route",
            needs_handoff=False,
            disclaimer_added=False,
            guardrail_result=None,
            degraded=False,
        )

    return None
