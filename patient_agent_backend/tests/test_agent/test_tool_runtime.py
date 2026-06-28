from app.agent.tool_runtime import normalize_tool_calls


def test_normalize_tool_calls_recovers_empty_tool_name():
    calls = [{"id": "call-1", "name": "", "args": {}}]

    normalized = normalize_tool_calls(calls, "我的挂号")

    assert normalized == [
        {
            "id": "call-1",
            "name": "query_registration",
            "args": {},
        }
    ]
