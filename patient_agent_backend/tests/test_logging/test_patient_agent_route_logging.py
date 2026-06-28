import json
import logging

import pytest
from langchain_core.messages import AIMessage

from app.agent.tool_runtime import run_tool_rounds
from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store


class FakeTool:
    def __init__(self, name, output):
        self.name = name
        self.output = output

    async def ainvoke(self, args):
        return self.output


class FakeLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    async def ainvoke(self, messages):
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_pre_route_logs_route_type(caplog, monkeypatch):
    import app.chat.pre_router as pre_router

    set_flow_state_store(InMemoryFlowStateStore())
    monkeypatch.setattr(
        pre_router,
        "_find_tool",
        lambda tool_name: FakeTool(
            "query_registration",
            json.dumps(
                {"ok": True, "summary": "共找到 1 条挂号记录", "data": [{"id": 9}]},
                ensure_ascii=False,
            ),
        )
        if tool_name == "query_registration"
        else None,
    )
    session = type("Session", (), {"patient_id": 88})()

    with caplog.at_level(logging.INFO):
        await pre_router.try_pre_route(
            session=session,
            thread_id="thread-1",
            user_message="我的挂号",
        )

    record = next(record for record in caplog.records if record.message == "pre_route_hit")
    assert record.route_type == "pre_route"
    assert record.tool_name == "query_registration"
    assert record.degraded is False


@pytest.mark.asyncio
async def test_tool_runtime_logs_error_type_for_graph_route(caplog):
    llm = FakeLLM([AIMessage(content="最终回复")])
    tool = FakeTool(
        "query_registration",
        json.dumps(
            {"ok": False, "error": "参数缺失: registration_id", "hint": "请补充记录ID"},
            ensure_ascii=False,
        ),
    )
    response = AIMessage(
        content="",
        tool_calls=[{"id": "call-1", "name": "query_registration", "args": {}}],
    )

    with caplog.at_level(logging.INFO):
        await run_tool_rounds(
            llm=llm,
            llm_messages=[],
            response=response,
            tools=[tool],
            last_user_content="取消挂号",
        )

    record = next(record for record in caplog.records if record.message == "tool_call_end")
    assert record.route_type == "graph_route"
    assert record.error_type == "validation_error"
    assert record.degraded is True
