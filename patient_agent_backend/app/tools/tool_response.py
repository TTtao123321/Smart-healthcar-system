"""工具统一返回格式辅助函数"""

import json
from typing import Any


def ok(summary: str, data: Any = None) -> str:
    """成功响应"""
    return json.dumps(
        {"ok": True, "summary": summary, "data": data},
        ensure_ascii=False,
        default=str,
    )


def err(error: str, hint: str = "") -> str:
    """失败响应。

    error: 错误简要描述
    hint: 给 LLM 的提示（如何向用户解释）
    """
    return json.dumps(
        {
            "ok": False,
            "error": error,
            "hint": hint or "请告知用户系统暂时无法处理该请求，不要编造任何数据。",
        },
        ensure_ascii=False,
    )


def empty(summary: str = "查询结果为空") -> str:
    """空结果响应（与 err 区分：调用成功但无数据）"""
    return json.dumps(
        {
            "ok": True,
            "summary": summary,
            "data": [],
            "hint": "查询成功但暂无相关数据，请如实告知用户。",
        },
        ensure_ascii=False,
    )
