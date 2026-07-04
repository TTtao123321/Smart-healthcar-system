"""临床病历草稿工具。"""

from langchain_core.tools import tool

from app.tools.tool_response import ok


def create_clinician_record_tools():
    @tool
    async def generate_record_draft(
        chief_complaint: str,
        patient_summary: str | None = None,
    ) -> str:
        """生成需要医生审核的病历草稿。"""
        present_illness = f"患者诉{chief_complaint}，症状待医生进一步核实。"
        if patient_summary:
            present_illness = f"{present_illness} 既往摘要：{patient_summary}"
        draft = {
            "draftId": "draft-1",
            "chiefComplaint": chief_complaint,
            "presentIllness": present_illness,
            "physicalExam": "生命体征待完善，建议结合门诊查体结果补充。",
            "disclaimer": "AI 草稿，仅供医生审核",
        }
        return ok("已生成病历草稿", draft)

    @tool
    async def build_insertable_record_payload(
        draft_id: str,
        sections: list[str],
    ) -> str:
        """根据草稿选择需要插入病历编辑器的字段。"""
        source = {
            "chiefComplaint": "咳嗽3天",
            "presentIllness": "患者诉咳嗽3天，症状待医生进一步核实。",
            "physicalExam": "生命体征待完善，建议结合门诊查体结果补充。",
        }
        payload = {key: value for key, value in source.items() if key in set(sections)}
        return ok(
            "已生成可插入病历载荷",
            {
                "draftId": draft_id,
                "recordPayload": payload,
                "disclaimer": "AI 草稿，仅供医生审核",
            },
        )

    return [
        generate_record_draft,
        build_insertable_record_payload,
    ]
