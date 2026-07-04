import json
import re
from typing import AsyncIterator, Callable

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.prompts import build_patient_system_prompt
from app.agent.request_context import set_patient_session, set_thread_id
from app.agent.state import AgentState
from app.chat.pre_router import try_pre_route
from app.logging_utils import get_request_logger, log_chat_result
from app.chat.models import ChatRunResult, ChatStreamEvent
from app.chat.output_filters import sanitize_visible_message
from app.clinician.context import set_clinician_context

logger = get_request_logger(__name__)


class ChatOrchestrator:
    def __init__(
        self,
        memory,
        graph_factory: Callable,
        *,
        channel: str = "patient",
        clinician_context=None,
    ):
        self._memory = memory
        self._graph_factory = graph_factory
        self._channel = channel
        self._clinician_context = clinician_context

    def _resolve_tools(self) -> list:
        from app.clinician.tool_registry import get_tools_for_channel

        return get_tools_for_channel(self._channel, self._clinician_context)

    def _resolve_system_prompt(self) -> str:
        if self._channel == "clinician" and self._clinician_context is not None:
            from app.clinician.prompts import build_clinician_system_prompt

            return build_clinician_system_prompt(self._clinician_context)
        return build_patient_system_prompt()

    def _create_graph(self):
        kwargs = {
            "tools": self._resolve_tools(),
            "system_prompt": self._resolve_system_prompt(),
            "channel": self._channel,
            "clinician_context": self._clinician_context,
        }
        try:
            return self._graph_factory(**kwargs)
        except TypeError:
            return self._graph_factory()

    async def _load_history(self, patient_id: int, thread_id: str) -> list[dict]:
        return await self._memory.load_messages(patient_id, thread_id)

    def _build_messages(self, history: list[dict], user_message: str) -> list:
        messages = []
        for item in history:
            if item.get("role") == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item.get("role") == "assistant":
                messages.append(AIMessage(content=item["content"]))
        messages.append(HumanMessage(content=user_message))
        return messages

    def _build_state(self, history: list[dict], user_message: str, patient_id: int) -> AgentState:
        return {
            "messages": self._build_messages(history, user_message),
            "patient_id": patient_id,
            "guardrail_result": None,
            "needs_handoff": False,
            "disclaimer_shown": False,
            "conversation_turn": len(history) // 2 + 1,
        }

    def _extract_reply(self, result: dict) -> str:
        result_messages = result.get("messages", [])
        reply = ""
        for msg in reversed(result_messages):
            if isinstance(msg, AIMessage) and msg.content:
                reply = msg.content
                break
        return sanitize_visible_message(reply)

    async def _save_history(
        self,
        *,
        patient_id: int,
        thread_id: str,
        history: list[dict],
        user_message: str,
        assistant_message: str,
    ) -> None:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})
        await self._memory.save_messages(patient_id, thread_id, history)
        if hasattr(self._memory, "save_thread_snapshot"):
            await self._memory.save_thread_snapshot(patient_id, thread_id, history)

    async def run_once(self, *, session, user_message: str, thread_id: str) -> ChatRunResult:
        set_patient_session(session)
        set_thread_id(thread_id)
        set_clinician_context(self._clinician_context)
        history = await self._load_history(session.patient_id, thread_id)
        pre_routed = None
        if self._channel == "patient":
            pre_routed = await try_pre_route(
                session=session,
                thread_id=thread_id,
                user_message=user_message,
            )
        if pre_routed is not None:
            await self._save_history(
                patient_id=session.patient_id,
                thread_id=thread_id,
                history=history,
                user_message=user_message,
                assistant_message=pre_routed.message,
            )
            log_chat_result(
                logger,
                guardrail_result=None,
                reply_type=pre_routed.reply_type,
                degraded=pre_routed.degraded,
            )
            return pre_routed

        state: AgentState = self._build_state(history, user_message, session.patient_id)

        result = await self._create_graph().ainvoke(state)
        raw_reply = ""
        raw_reply_type = "none"
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                raw_reply = str(msg.content)
                raw_reply_type = type(msg.content).__name__
                break
        reply = self._extract_reply(result)
        logger.info(
            "chat_reply_extracted",
            extra={
                "raw_reply_type": raw_reply_type,
                "raw_reply_preview": raw_reply[:200],
                "cleaned_reply_preview": reply[:200],
            },
        )
        await self._save_history(
            patient_id=session.patient_id,
            thread_id=thread_id,
            history=history,
            user_message=user_message,
            assistant_message=reply,
        )
        log_chat_result(
            logger,
            guardrail_result=result.get("guardrail_result"),
            reply_type="normal",
            degraded=False,
        )

        return ChatRunResult(
            thread_id=thread_id,
            message=reply,
            reply_type="normal",
            needs_handoff=bool(result.get("needs_handoff", False)),
            disclaimer_added=False,
            guardrail_result=result.get("guardrail_result"),
            degraded=False,
        )

    async def run_stream(
        self,
        *,
        session,
        user_message: str,
        thread_id: str,
    ) -> AsyncIterator[ChatStreamEvent]:
        set_patient_session(session)
        set_thread_id(thread_id)
        set_clinician_context(self._clinician_context)
        history = await self._load_history(session.patient_id, thread_id)
        pre_routed = None
        if self._channel == "patient":
            pre_routed = await try_pre_route(
                session=session,
                thread_id=thread_id,
                user_message=user_message,
            )
        if pre_routed is not None:
            await self._save_history(
                patient_id=session.patient_id,
                thread_id=thread_id,
                history=history,
                user_message=user_message,
                assistant_message=pre_routed.message,
            )
            log_chat_result(
                logger,
                guardrail_result=None,
                reply_type=pre_routed.reply_type,
                degraded=pre_routed.degraded,
            )
            yield ChatStreamEvent(
                event="message",
                data={"content": pre_routed.message, "thread_id": thread_id},
            )
            yield ChatStreamEvent(event="done", data={"thread_id": thread_id})
            return

        state: AgentState = self._build_state(history, user_message, session.patient_id)
        graph = self._create_graph()

        try:
            visible_response = ""
            think_state = "outside"
            think_buffer = ""
            tool_started = False
            pending_pre_tool_message = ""
            final_result = None

            async for event in graph.astream_events(state, version="v2"):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        think_buffer += chunk.content
                        while True:
                            if think_state == "outside":
                                idx = think_buffer.find("<think>")
                                if idx == -1:
                                    safe_len = max(len(think_buffer) - 6, 0)
                                    if safe_len > 0:
                                        emit = think_buffer[:safe_len]
                                        think_buffer = think_buffer[safe_len:]
                                        if not tool_started:
                                            pending_pre_tool_message += emit
                                        else:
                                            visible_response += emit
                                    break
                                if idx > 0:
                                    emit = think_buffer[:idx]
                                    if not tool_started:
                                        pending_pre_tool_message += emit
                                    else:
                                        visible_response += emit
                                think_buffer = think_buffer[idx + len("<think>"):]
                                think_state = "inside"
                            else:
                                idx = think_buffer.find("</think>")
                                if idx == -1:
                                    safe_len = max(len(think_buffer) - 7, 0)
                                    if safe_len > 0:
                                        emit = think_buffer[:safe_len]
                                        think_buffer = think_buffer[safe_len:]
                                        yield ChatStreamEvent(
                                            event="thinking",
                                            data={"content": emit, "thread_id": thread_id},
                                        )
                                    break
                                if idx > 0:
                                    emit = think_buffer[:idx]
                                    yield ChatStreamEvent(
                                        event="thinking",
                                        data={"content": emit, "thread_id": thread_id},
                                    )
                                think_buffer = think_buffer[idx + len("</think>"):]
                                think_state = "outside"

                elif kind == "on_tool_start":
                    tool_started = True
                    if pending_pre_tool_message.strip():
                        cleaned_reasoning = re.sub(
                            r"^\s*think[:：]?\s*",
                            "",
                            pending_pre_tool_message,
                            flags=re.IGNORECASE,
                        )
                        yield ChatStreamEvent(
                            event="thinking",
                            data={"content": cleaned_reasoning, "thread_id": thread_id},
                        )
                        pending_pre_tool_message = ""
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    run_id = event.get("run_id", "")
                    safe_args = {}
                    for key, value in tool_input.items():
                        try:
                            json.dumps(value)
                            safe_args[key] = value
                        except (TypeError, ValueError):
                            safe_args[key] = str(value)
                    yield ChatStreamEvent(
                        event="tool_start",
                        data={
                            "tool_call_id": run_id,
                            "tool_name": tool_name,
                            "tool_args": safe_args,
                        },
                    )

                elif kind == "on_tool_end":
                    yield ChatStreamEvent(
                        event="tool_end",
                        data={
                            "tool_call_id": event.get("run_id", ""),
                            "tool_name": event.get("name", "unknown"),
                            "tool_result": str(event.get("data", {}).get("output") or ""),
                        },
                    )

                elif kind == "on_tool_error":
                    err = event.get("data", {}).get("error") or event.get("data", {}).get("output")
                    yield ChatStreamEvent(
                        event="tool_end",
                        data={
                            "tool_call_id": event.get("run_id", ""),
                            "tool_name": event.get("name", "unknown"),
                            "tool_error": str(err) if err is not None else "工具调用失败",
                        },
                    )
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict) and output.get("messages"):
                        final_result = output

            if think_buffer:
                if think_state == "outside":
                    if not tool_started:
                        pending_pre_tool_message += think_buffer
                    else:
                        visible_response += think_buffer
                else:
                    yield ChatStreamEvent(
                        event="thinking",
                        data={"content": think_buffer, "thread_id": thread_id},
                    )

            if not tool_started and pending_pre_tool_message.strip():
                clean_emit = sanitize_visible_message(pending_pre_tool_message)
                visible_response += clean_emit
                yield ChatStreamEvent(
                    event="message",
                    data={"content": clean_emit, "thread_id": thread_id},
                )

            final_message = (
                self._extract_reply(final_result)
                if final_result is not None
                else sanitize_visible_message(visible_response.strip())
            )
            if tool_started and final_message:
                yield ChatStreamEvent(
                    event="message",
                    data={"content": final_message, "thread_id": thread_id},
                )
            await self._save_history(
                patient_id=session.patient_id,
                thread_id=thread_id,
                history=history,
                user_message=user_message,
                assistant_message=final_message,
            )
            log_chat_result(
                logger,
                guardrail_result=None,
                reply_type="stream",
                degraded=False,
            )
            yield ChatStreamEvent(event="done", data={"thread_id": thread_id})
        except Exception as exc:
            logger.error("Agent 流式执行失败: %s", exc, exc_info=True)
            log_chat_result(
                logger,
                guardrail_result=None,
                reply_type="stream_error",
                degraded=True,
            )
            yield ChatStreamEvent(
                event="message",
                data={"content": "智能助手暂时无法响应，请稍后再试。", "thread_id": thread_id},
            )
            yield ChatStreamEvent(event="done", data={"thread_id": thread_id})
