"""Agent 状态定义"""

from typing import TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """LangGraph Agent 状态"""
    messages: list[BaseMessage]       # 对话历史
    patient_id: str | None            # 当前患者 ID
    guardrail_result: str | None      # 护栏检查结果
    needs_handoff: bool               # 是否需要转人工
    disclaimer_shown: bool            # 是否已展示免责声明
    conversation_turn: int            # 当前对话轮次
