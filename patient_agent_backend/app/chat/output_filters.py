import re


TOOL_TAG_PATTERN = re.compile(r"<tool_calls?>.*?</tool_calls?>", re.IGNORECASE | re.DOTALL)
THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
PLAIN_THINK_LINE_PATTERN = re.compile(r"^\s*think(?:\b|[:：]).*$", re.IGNORECASE)
PROTOCOL_LINE_PATTERN = re.compile(
    r"^\s*(查询医生列表|查询科室列表|查询医生排班|查询排班详情|查询挂号|创建挂号|取消挂号|成功|失败|调用中)\s*$"
)


def sanitize_visible_message(content: str) -> str:
    cleaned = THINK_TAG_PATTERN.sub("", content or "")
    cleaned = TOOL_TAG_PATTERN.sub("", cleaned)
    filtered_lines = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if PLAIN_THINK_LINE_PATTERN.match(stripped):
            continue
        if PROTOCOL_LINE_PATTERN.match(stripped):
            continue
        filtered_lines.append(line.rstrip())
    cleaned = "\n".join(filtered_lines).strip()
    return cleaned or "系统暂时无法处理该请求，请稍后再试。"
