import json

import pytest

from app.tools.clinician_record_tools import create_clinician_record_tools


@pytest.mark.asyncio
async def test_generate_record_draft_marks_output_as_review_required():
    tools = create_clinician_record_tools()
    generate_record_draft = next(tool for tool in tools if tool.name == "generate_record_draft")

    response = await generate_record_draft.ainvoke({"chief_complaint": "咳嗽3天"})
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["data"]["chiefComplaint"] == "咳嗽3天"
    assert payload["data"]["disclaimer"] == "AI 草稿，仅供医生审核"


@pytest.mark.asyncio
async def test_build_insertable_record_payload_only_keeps_selected_sections():
    tools = create_clinician_record_tools()
    build_insertable_record_payload = next(
        tool for tool in tools if tool.name == "build_insertable_record_payload"
    )

    response = await build_insertable_record_payload.ainvoke(
        {
            "draft_id": "draft-1",
            "sections": ["chiefComplaint", "physicalExam"],
        }
    )
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["data"]["draftId"] == "draft-1"
    assert set(payload["data"]["recordPayload"].keys()) == {"chiefComplaint", "physicalExam"}
