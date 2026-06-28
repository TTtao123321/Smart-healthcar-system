from types import SimpleNamespace
from langchain_core.messages import AIMessage
from unittest.mock import AsyncMock

from app.chat.orchestrator import ChatOrchestrator
from app.chat.models import ChatRunResult


class FakeMemory:
    def __init__(self):
        self.saved = None
        self.snapshot = None

    async def load_messages(self, patient_id, thread_id):
        return [{"role": "assistant", "content": "历史消息"}]

    async def save_messages(self, patient_id, thread_id, history):
        self.saved = (patient_id, thread_id, history)

    async def save_thread_snapshot(self, patient_id, thread_id, history):
        self.snapshot = (patient_id, thread_id, history)


class FakeGraph:
    def __init__(self):
        self.state = None

    async def ainvoke(self, state):
        self.state = state
        return {"messages": [AIMessage(content="统一回复")], "needs_handoff": False}


class FakeSession:
    patient_id = 9
    token = "t"
    name = "张三"
    phone = "13800138000"


async def test_run_once_uses_session_patient_id_and_persists_history():
    graph = FakeGraph()
    memory = FakeMemory()
    orchestrator = ChatOrchestrator(memory=memory, graph_factory=lambda: graph)

    result = await orchestrator.run_once(
        session=FakeSession(),
        user_message="我要挂号",
        thread_id="thread-1",
    )

    assert graph.state["patient_id"] == 9
    assert result.message == "统一回复"
    assert result.thread_id == "thread-1"
    assert result.reply_type == "normal"
    assert memory.saved[0] == 9
    assert memory.saved[1] == "thread-1"
    assert memory.snapshot[0] == 9
    assert memory.snapshot[1] == "thread-1"


async def test_run_once_uses_pre_router_before_graph(monkeypatch):
    graph = FakeGraph()
    memory = FakeMemory()
    orchestrator = ChatOrchestrator(memory=memory, graph_factory=lambda: graph)
    monkeypatch.setattr(
        "app.chat.orchestrator.try_pre_route",
        AsyncMock(
            return_value=ChatRunResult(
                thread_id="thread-2",
                message="前置路由回复",
                reply_type="pre_route",
                needs_handoff=False,
                disclaimer_added=False,
                guardrail_result=None,
                degraded=False,
            )
        ),
    )

    result = await orchestrator.run_once(
        session=FakeSession(),
        user_message="我的挂号",
        thread_id="thread-2",
    )

    assert result.reply_type == "pre_route"
    assert result.message == "前置路由回复"
    assert graph.state is None
    assert memory.saved[1] == "thread-2"


class FakeStreamGraph:
    async def astream_events(self, state, version="v2"):
        yield {
            "event": "on_tool_start",
            "name": "query_doctor_schedules",
            "run_id": "tool-1",
            "data": {"input": {"doctor_name": "韩倩倩", "date": "今天上午"}},
        }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "data": {
                "chunk": SimpleNamespace(
                    content="查询医生排班\n成功\n最后挂号。\nthink 用户想预约韩倩倩医生今天上午的号。\nules。\n"
                )
            },
        }
        yield {
            "event": "on_tool_end",
            "name": "query_doctor_schedules",
            "run_id": "tool-1",
            "data": {"output": '{"ok": true, "summary": "近期无排班数据"}'},
        }
        yield {
            "event": "on_chain_end",
            "name": "LangGraph",
            "data": {
                "output": {
                    "messages": [
                        AIMessage(
                            content=(
                                "韩倩倩医生（口腔科）今天上午排班详情如下：\n"
                                "- 时段1：已约1人／剩余9个号"
                            )
                        )
                    ],
                    "needs_handoff": False,
                }
            },
        }


async def test_run_stream_prefers_final_graph_reply_after_tool_events(monkeypatch):
    memory = FakeMemory()
    orchestrator = ChatOrchestrator(memory=memory, graph_factory=lambda: FakeStreamGraph())
    monkeypatch.setattr("app.chat.orchestrator.try_pre_route", AsyncMock(return_value=None))

    events = [
        event
        async for event in orchestrator.run_stream(
            session=FakeSession(),
            user_message="帮我预约韩倩倩今天上午的号",
            thread_id="thread-stream-1",
        )
    ]

    message_events = [event for event in events if event.event == "message"]
    assert len(message_events) == 1
    assert message_events[0].data["content"] == (
        "韩倩倩医生（口腔科）今天上午排班详情如下：\n"
        "- 时段1：已约1人／剩余9个号"
    )
    assert "think 用户" not in message_events[0].data["content"]
    assert "最后挂号" not in message_events[0].data["content"]
    assert memory.saved[2][-1]["content"] == message_events[0].data["content"]
