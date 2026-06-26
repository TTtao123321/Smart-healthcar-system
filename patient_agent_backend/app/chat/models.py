from dataclasses import dataclass
from typing import Any


@dataclass
class ChatRunResult:
    thread_id: str
    message: str
    reply_type: str
    needs_handoff: bool
    disclaimer_added: bool
    guardrail_result: str | None
    degraded: bool


@dataclass
class ChatStreamEvent:
    event: str
    data: dict[str, Any]
