from app.chat.output_filters import sanitize_visible_message


def test_sanitize_visible_message_removes_tool_tags():
    raw = '<tool_calls>{"name":"query_registration"}</tool_calls>抱歉，请稍后再试'

    assert sanitize_visible_message(raw) == "抱歉，请稍后再试"


def test_sanitize_visible_message_falls_back_when_content_becomes_empty():
    raw = '<tool_call>{"name":"query_registration"}</tool_call>'

    assert sanitize_visible_message(raw) == "系统暂时无法处理该请求，请稍后再试。"


def test_sanitize_visible_message_removes_think_tags():
    raw = "<think>内部思考，不应展示</think>暂时无法获取该信息，请稍后再试。"

    assert sanitize_visible_message(raw) == "暂时无法获取该信息，请稍后再试。"
