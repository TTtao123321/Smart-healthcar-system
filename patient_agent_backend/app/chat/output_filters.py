import re


TOOL_TAG_PATTERN = re.compile(r"<tool_calls?>.*?</tool_calls?>", re.IGNORECASE | re.DOTALL)


def sanitize_visible_message(content: str) -> str:
    cleaned = TOOL_TAG_PATTERN.sub("", content or "").strip()
    return cleaned or "系统暂时无法处理该请求，请稍后再试。"
