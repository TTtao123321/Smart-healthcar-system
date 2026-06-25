from app.agent.nodes import recover_tool_call


def test_recover_tool_call_for_departments():
    tool_call = recover_tool_call("医院有哪些科室？")

    assert tool_call == {
        "name": "query_departments",
        "args": {},
    }


def test_recover_tool_call_for_doctors_by_department():
    tool_call = recover_tool_call("内科有哪些医生出诊？")

    assert tool_call == {
        "name": "query_doctors",
        "args": {"dept_name": "内科"},
    }
