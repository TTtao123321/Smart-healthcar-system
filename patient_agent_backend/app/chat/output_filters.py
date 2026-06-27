import re


TOOL_TAG_PATTERN = re.compile(r"<tool_calls?>.*?</tool_calls?>", re.IGNORECASE | re.DOTALL)
THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def sanitize_visible_message(content: str) -> str:
    cleaned = THINK_TAG_PATTERN.sub("", content or "")
    cleaned = TOOL_TAG_PATTERN.sub("", cleaned).strip()
    return cleaned or "系统暂时无法处理该请求，请稍后再试。"
