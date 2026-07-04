from app.agent.tool_runtime import normalize_tool_calls
from app.clinician.models import ClinicianContext
from app.clinician.tool_registry import get_tools_for_channel


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


def test_clinician_channel_uses_clinician_tool_whitelist():
    context = ClinicianContext(
        user_id=9,
        role_codes=["DOCTOR"],
        dept_scope=[3],
        doctor_scope=[12],
    )

    tools = get_tools_for_channel("clinician", context)
    tool_names = {tool.name for tool in tools}

    assert "query_patient_medical_records" in tool_names
    assert "create_registration" not in tool_names
