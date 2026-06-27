from app.guardrails.output_guard import DISCLAIMER, check_output


def test_check_output_appends_disclaimer_once():
    message, shown = check_output(
        "建议你先休息。",
        needs_disclaimer=True,
        disclaimer_shown=False,
    )

    assert DISCLAIMER in message
    assert shown is True


def test_check_output_does_not_duplicate_disclaimer():
    message, shown = check_output(
        "以上信息请以医院安排为准。",
        needs_disclaimer=True,
        disclaimer_shown=True,
    )

    assert message == "以上信息请以医院安排为准。"
    assert shown is True
