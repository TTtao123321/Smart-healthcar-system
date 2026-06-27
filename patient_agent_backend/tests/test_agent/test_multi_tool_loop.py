from langchain_core.messages import AIMessage, HumanMessage
import pytest

from app.agent.nodes import agent


class FakeLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    async def ainvoke(self, messages):
        assert self._responses, "no more fake llm responses configured"
        return self._responses.pop(0)


class FakeTool:
    def __init__(self, name, result):
        self.name = name
        self.result = result
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)
        return self.result


@pytest.mark.asyncio
async def test_agent_executes_multiple_tool_rounds(monkeypatch):
    schedule_tool = FakeTool(
        "query_doctor_schedules",
        '{"ok": true, "summary": "找到排班", "data": [{"workPlanId": 217}]}',
    )
    detail_tool = FakeTool(
        "query_schedule_detail",
        '{"ok": true, "summary": "排班详情", "data": {"work_plan_id": 217, "doctor_schedule_id": 951, "slot": 1}}',
    )

    llm_with_tools = FakeLLM(
        [
            AIMessage(
                content="",
                    tool_calls=[{
                        "id": "call-1",
                        "name": "query_doctor_schedules",
                        "args": {"doctor_name": "袁文斌", "dept_name": "口腔科"},
                    }],
            ),
            AIMessage(
                content="",
                    tool_calls=[{
                        "id": "call-2",
                        "name": "query_schedule_detail",
                        "args": {"work_plan_id": 217},
                    }],
            ),
            AIMessage(content="已为您确认到可用时段，下一步可创建挂号。"),
        ]
    )

    def fake_get_llm(tools=None):
        return llm_with_tools

    monkeypatch.setattr("app.agent.nodes._get_llm", fake_get_llm)

    result = await agent(
        {
            "messages": [HumanMessage(content="请帮我确认挂号")],
            "guardrail_result": None,
        },
        [schedule_tool, detail_tool],
    )

    assert schedule_tool.calls == [{"doctor_name": "袁文斌", "dept_name": "口腔科"}]
    assert detail_tool.calls == [{"work_plan_id": 217}]
    assert result["messages"][0].content == "已为您确认到可用时段，下一步可创建挂号。"
