from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.request_context import set_patient_session
from app.agent.state import AgentState
from app.chat.models import ChatRunResult


class ChatOrchestrator:
    def __init__(self, memory, graph_factory: Callable):
        self._memory = memory
        self._graph_factory = graph_factory

    async def run_once(self, *, session, user_message: str, thread_id: str) -> ChatRunResult:
        set_patient_session(session)
        history = await self._memory.load_messages(session.patient_id, thread_id)

        messages = []
        for item in history:
            if item.get("role") == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item.get("role") == "assistant":
                messages.append(AIMessage(content=item["content"]))
        messages.append(HumanMessage(content=user_message))

        state: AgentState = {
            "messages": messages,
            "patient_id": session.patient_id,
            "guardrail_result": None,
            "needs_handoff": False,
            "disclaimer_shown": False,
            "conversation_turn": len(history) // 2 + 1,
        }

        result = await self._graph_factory().ainvoke(state)
        result_messages = result.get("messages", [])
        reply = ""
        for msg in reversed(result_messages):
            if isinstance(msg, AIMessage) and msg.content:
                reply = msg.content
                break

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        await self._memory.save_messages(session.patient_id, thread_id, history)

        return ChatRunResult(
            thread_id=thread_id,
            message=reply,
            reply_type="normal",
            needs_handoff=bool(result.get("needs_handoff", False)),
            disclaimer_added=False,
            guardrail_result=result.get("guardrail_result"),
            degraded=False,
        )
