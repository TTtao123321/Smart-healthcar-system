import json

import pytest

from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store


class FakeTool:
    def __init__(self, name, output):
        self.name = name
        self.output = output
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)
        return self.output


@pytest.mark.asyncio
async def test_pre_router_routes_query_registration(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    query_tool = FakeTool(
        "query_registration",
        json.dumps(
            {
                "ok": True,
                "summary": "共找到 1 条挂号记录",
                "data": [{"id": 9, "appointment_date": "2026-06-26", "slot": 1}],
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(pre_router, "_find_tool", lambda tool_name: query_tool if tool_name == "query_registration" else None)
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-1",
        user_message="我的挂号",
    )

    assert result is not None
    assert result.reply_type == "pre_route"
    assert "共找到 1 条挂号记录" in result.message
    assert query_tool.calls == [{}]


@pytest.mark.asyncio
async def test_pre_router_routes_my_prescriptions(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    prescription_tool = FakeTool(
        "query_my_prescriptions",
        json.dumps(
            {
                "ok": True,
                "summary": "已查询到处方记录",
                "data": [{"prescriptionId": 18, "visitDate": "2026-06-26"}],
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(
        pre_router,
        "_find_tool",
        lambda tool_name: prescription_tool if tool_name == "query_my_prescriptions" else None,
    )
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-rx-1",
        user_message="我的处方",
    )

    assert result is not None
    assert result.reply_type == "pre_route"
    assert "已查询到处方记录" in result.message
    assert prescription_tool.calls == [{}]


@pytest.mark.asyncio
async def test_pre_router_formats_sidebar_medical_record_detail(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    detail_tool = FakeTool(
        "get_medical_record_detail",
        json.dumps(
            {
                "ok": True,
                "summary": "已查询到病历详情",
                "data": {
                    "medicalRecordId": 8,
                    "visitDate": "2026-06-15",
                    "department": "皮肤病门诊",
                    "doctorName": "王医生",
                    "chiefComplaint": "皮疹 3 天",
                    "diagnosisSummary": "接触性皮炎",
                    "instructionSummary": "避免抓挠，按医嘱用药",
                },
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(
        pre_router,
        "_find_tool",
        lambda tool_name: detail_tool if tool_name == "get_medical_record_detail" else None,
    )
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-record-detail",
        user_message=json.dumps(
            {
                "source": "patient_sidebar",
                "action": "view_recent_medical_record",
                "payload": {"medical_record_id": 8},
            },
            ensure_ascii=False,
        ),
    )

    assert result is not None
    assert "已查询到病历详情" in result.message
    assert "就诊日期：2026-06-15" in result.message
    assert "科室：皮肤病门诊" in result.message
    assert "主诉：皮疹 3 天" in result.message
    assert "诊断摘要：接触性皮炎" in result.message
    assert "医嘱摘要：避免抓挠，按医嘱用药" in result.message
    assert detail_tool.calls == [{"medical_record_id": 8}]


@pytest.mark.asyncio
async def test_pre_router_routes_sidebar_prescription_action(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    detail_tool = FakeTool(
        "get_prescription_detail",
        json.dumps(
            {
                "ok": True,
                "summary": "已查询到处方详情",
                "data": {
                    "prescriptionId": 18,
                    "visitDate": "2026-06-15",
                    "department": "皮肤病门诊",
                    "doctorName": "王医生",
                    "diagnosis": "接触性皮炎",
                    "doctorAdvice": "外用药物，避免刺激",
                    "items": [
                        {
                            "drugName": "炉甘石洗剂",
                            "specification": "100ml",
                            "quantity": 1,
                            "dosage": "外用适量",
                            "frequency": "每日2次",
                            "days": 7,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(
        pre_router,
        "_find_tool",
        lambda tool_name: detail_tool if tool_name == "get_prescription_detail" else None,
    )
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-rx-2",
        user_message=json.dumps(
            {
                "source": "patient_sidebar",
                "action": "view_recent_prescription",
                "payload": {"prescription_id": 18},
            },
            ensure_ascii=False,
        ),
    )

    assert result is not None
    assert "已查询到处方详情" in result.message
    assert "诊断：接触性皮炎" in result.message
    assert "医嘱：外用药物，避免刺激" in result.message
    assert "炉甘石洗剂" in result.message
    assert "外用适量" in result.message
    assert detail_tool.calls == [{"prescription_id": 18}]


@pytest.mark.asyncio
async def test_pre_router_routes_cancel_registration(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    query_tool = FakeTool(
        "query_registration",
        json.dumps(
            {
                "ok": True,
                "summary": "共找到 2 条挂号记录",
                "data": [
                    {"id": 9, "appointment_date": "2026-06-26", "slot": 1},
                    {"id": 10, "appointment_date": "2026-06-27", "slot": 2},
                ],
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(pre_router, "_find_tool", lambda tool_name: query_tool if tool_name == "query_registration" else None)
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-1",
        user_message="取消挂号",
    )

    assert result is not None
    assert "请告诉我想取消哪一条挂号记录" in result.message
    assert query_tool.calls == [{}]


@pytest.mark.asyncio
async def test_pre_router_routes_confirmation_when_pending_state_exists(monkeypatch):
    import app.chat.pre_router as pre_router

    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    await store.save(
        "patient:8:thread-2",
        {
            "pending_registration_confirmation": {
                "work_plan_id": 11,
                "doctor_schedule_id": 22,
                "doctor_id": 33,
                "dept_sub_id": 44,
                "appointment_date": "2026-06-28",
                "slot": 1,
                "schedule_options": [
                    {"doctor_schedule_id": 22, "slot": 1},
                    {"doctor_schedule_id": 23, "slot": 2},
                ],
            }
        },
    )
    create_tool = FakeTool(
        "create_registration",
        json.dumps({"ok": True, "summary": "挂号成功", "data": {"id": 101}}, ensure_ascii=False),
    )
    monkeypatch.setattr(pre_router, "_find_tool", lambda tool_name: create_tool if tool_name == "create_registration" else None)
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-2",
        user_message="选第 2 个",
    )

    assert result is not None
    assert "挂号成功" in result.message
    assert create_tool.calls == [{"slot": 2}]


@pytest.mark.asyncio
async def test_pre_router_returns_none_when_not_matched(monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    monkeypatch.setattr(pre_router, "_find_tool", lambda tool_name: None)
    session = type("Session", (), {"patient_id": 8})()

    result = await pre_router.try_pre_route(
        session=session,
        thread_id="thread-3",
        user_message="内科有哪些医生",
    )

    assert result is None
