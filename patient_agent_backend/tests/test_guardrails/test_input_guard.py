from app.guardrails.input_guard import check_input


def test_check_input_blocks_diagnosis_request():
    result = check_input("请你帮我判断是不是肺炎")

    assert result.blocked is True
    assert result.reason == "diagnosis_request"


def test_check_input_marks_health_topic_for_disclaimer():
    result = check_input("最近一直咳嗽，想了解应该挂什么科")

    assert result.blocked is False
    assert result.needs_disclaimer is True
    assert result.reason == "health_topic"
