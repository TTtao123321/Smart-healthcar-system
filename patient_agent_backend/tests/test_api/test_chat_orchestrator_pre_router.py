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
