from langchain_core.messages import AIMessage

from app.chat.orchestrator import ChatOrchestrator


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
