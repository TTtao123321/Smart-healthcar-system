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


def test_sanitize_visible_message_removes_plain_think_trace_and_protocol_lines():
    raw = """查询医生列表
成功
think:用户询问“内科有哪些医生出诊”，已通过 query_doctors 获取到医生名单。
内科共有17位医生出诊，名单如下：
- 李雨萌（副主任医师）
"""

    assert sanitize_visible_message(raw) == """内科共有17位医生出诊，名单如下：
- 李雨萌（副主任医师）"""


def test_sanitize_visible_message_removes_plain_think_trace_without_colon():
    raw = """think 用户想预约韩倩倩医生今天上午的号。
韩倩倩医生（口腔科）今天上午排班详情如下：
- 时段1：已约1人／剩余9个号
"""

    assert sanitize_visible_message(raw) == """韩倩倩医生（口腔科）今天上午排班详情如下：
- 时段1：已约1人／剩余9个号"""
