# Patient Agent Orchestration Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 收口患者聊天与侧栏主链路，稳定支持挂号闭环，并统一护栏、降级、日志、测试与 CORS/配置策略。

**Architecture:** 保留现有 LangGraph、工具与 HMS client，不重写底层模型调用，只在 API 与 graph 之间新增统一编排层。普通接口、SSE、侧栏动作都通过同一 orchestration service 进入业务主链路，再用线程级轻量流程上下文维持挂号闭环状态。

**Tech Stack:** FastAPI, LangGraph, LangChain, Redis, aiomysql, Pydantic Settings, React 19, Vite, pytest

## Global Constraints

- 保留当前可用的 LangGraph 和工具体系，不重做底层能力。
- 第一阶段不引入复杂状态机框架，只增加线程级轻量流程上下文。
- 不新增“常用就诊人”“代他人挂号”等多身份能力。
- 查询和取消挂号始终使用认证会话里的当前患者身份。
- 普通接口与 SSE 必须命中同一套输入护栏、输出护栏、免责声明和转人工逻辑。
- HMS、Redis、LLM、未知异常都必须返回明确降级响应，不得直接向前端暴露裸 500。
- 生产环境不允许 `allow_origins=["*"]`。
- 不允许 `allow_credentials=True` 与 `*` 组合。
- 异常响应不得暴露内部堆栈、原始异常文本或系统细节。

---

### Task 1: 提取统一编排层

**Files:**
- Create: `patient_agent_backend/app/chat/__init__.py`
- Create: `patient_agent_backend/app/chat/models.py`
- Create: `patient_agent_backend/app/chat/orchestrator.py`
- Test: `patient_agent_backend/tests/test_api/test_chat_orchestrator.py`

**Interfaces:**
- Consumes: `compile_graph()`, `RedisMemory.load_messages()`, `RedisMemory.save_messages()`, `PatientSession`
- Produces: `ChatRunResult`, `ChatStreamEvent`, `ChatOrchestrator.run_once()`, `ChatOrchestrator.run_stream()`

- [ ] **Step 1: 写失败测试，锁定统一编排层的输入输出**

```python
from langchain_core.messages import AIMessage

from app.chat.orchestrator import ChatOrchestrator


class FakeMemory:
    async def load_messages(self, patient_id, thread_id):
        return [{"role": "assistant", "content": "历史消息"}]

    async def save_messages(self, patient_id, thread_id, history):
        self.saved = (patient_id, thread_id, history)


class FakeGraph:
    async def ainvoke(self, state):
        return {"messages": [AIMessage(content="统一回复")], "needs_handoff": False}


async def test_run_once_uses_session_patient_id_and_persists_history():
    orchestrator = ChatOrchestrator(memory=FakeMemory(), graph_factory=lambda: FakeGraph())

    result = await orchestrator.run_once(
        session=type("S", (), {"patient_id": 9, "token": "t", "name": "张三", "phone": "13800138000"})(),
        user_message="我要挂号",
        thread_id="thread-1",
    )

    assert result.message == "统一回复"
    assert result.thread_id == "thread-1"
    assert result.reply_type == "normal"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api/test_chat_orchestrator.py -v`

Expected: FAIL，提示 `ModuleNotFoundError: No module named 'app.chat'` 或 `ChatOrchestrator` 未定义。

- [ ] **Step 3: 写最小实现，定义统一编排层接口**

```python
from dataclasses import dataclass
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.request_context import set_patient_session
from app.agent.state import AgentState


@dataclass
class ChatRunResult:
    thread_id: str
    message: str
    reply_type: str
    needs_handoff: bool
    disclaimer_added: bool
    guardrail_result: str | None
    degraded: bool


@dataclass
class ChatStreamEvent:
    event: str
    data: dict[str, Any]


class ChatOrchestrator:
    def __init__(self, memory, graph_factory):
        self._memory = memory
        self._graph_factory = graph_factory

    async def run_once(self, *, session, user_message: str, thread_id: str) -> ChatRunResult:
        set_patient_session(session)
        history = await self._memory.load_messages(session.patient_id, thread_id)
        messages = [AIMessage(content=m["content"]) for m in history if m["role"] == "assistant"]
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
        reply = next((m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content), "")
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})
        await self._memory.save_messages(session.patient_id, thread_id, history)
        return ChatRunResult(
            thread_id=thread_id,
            message=reply,
            reply_type="normal",
            needs_handoff=bool(result.get("needs_handoff")),
            disclaimer_added=False,
            guardrail_result=result.get("guardrail_result"),
            degraded=False,
        )

    async def run_stream(self, *, session, user_message: str, thread_id: str) -> AsyncIterator[ChatStreamEvent]:
        raise NotImplementedError
```

- [ ] **Step 4: 运行测试，确认最小实现通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api/test_chat_orchestrator.py -v`

Expected: PASS，且断言 `result.message == "统一回复"` 与 `result.thread_id == "thread-1"` 成立。

- [ ] **Step 5: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/chat/__init__.py \
  patient_agent_backend/app/chat/models.py \
  patient_agent_backend/app/chat/orchestrator.py \
  patient_agent_backend/tests/test_api/test_chat_orchestrator.py
git commit -m "feat(chat): add shared orchestration layer"
```

### Task 2: 统一普通接口与 SSE，收口错误降级与 `<tool_calls>` 清洗

**Files:**
- Modify: `patient_agent_backend/app/api/chat.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Create: `patient_agent_backend/app/chat/output_filters.py`
- Test: `patient_agent_backend/tests/test_api/test_chat_stream_api.py`
- Test: `patient_agent_backend/tests/test_guardrails/test_chat_output_filters.py`

**Interfaces:**
- Consumes: `ChatOrchestrator.run_once()`, `ChatOrchestrator.run_stream()`, `check_output()`
- Produces: `sanitize_visible_message(content: str) -> str`, SSE `message/tool_start/tool_end/done/error` 统一输出，普通接口和 SSE 共用的降级文案

- [ ] **Step 1: 写失败测试，覆盖 `<tool_calls>` 泄露和流式错误降级**

```python
from app.chat.output_filters import sanitize_visible_message


def test_sanitize_visible_message_removes_tool_tags():
    raw = '<tool_calls>{"name":"query_registration"}</tool_calls>抱歉，请稍后再试'
    assert sanitize_visible_message(raw) == "抱歉，请稍后再试"


def test_sanitize_visible_message_falls_back_when_content_becomes_empty():
    raw = '<tool_call>{"name":"query_registration"}</tool_call>'
    assert sanitize_visible_message(raw) == "系统暂时无法处理该请求，请稍后再试。"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_guardrails/test_chat_output_filters.py -v`

Expected: FAIL，提示 `app.chat.output_filters` 不存在，或 `<tool_calls>` 仍原样输出。

- [ ] **Step 3: 写最小实现，统一清洗逻辑并把 API 改成只调用 orchestrator**

```python
import re


TOOL_TAG_PATTERN = re.compile(r"<tool_calls?>.*?</tool_calls?>", re.IGNORECASE | re.DOTALL)


def sanitize_visible_message(content: str) -> str:
    cleaned = TOOL_TAG_PATTERN.sub("", content or "").strip()
    return cleaned or "系统暂时无法处理该请求，请稍后再试。"
```

```python
@router.post("")
async def chat(request: Request, session: PatientSession = Depends(require_patient_session)):
    body = await request.json()
    result = await get_orchestrator().run_once(
        session=session,
        user_message=body.get("message", ""),
        thread_id=body.get("thread_id") or str(uuid.uuid4()),
    )
    return {
        "message": result.message,
        "thread_id": result.thread_id,
        "needs_handoff": result.needs_handoff,
        "reply_type": result.reply_type,
        "degraded": result.degraded,
    }
```

- [ ] **Step 4: 写失败测试，覆盖流式事件与普通接口同源**

```python
def test_chat_stream_returns_degraded_error_message(client):
    response = client.post(
        "/api/chat/stream",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "我要挂号", "thread_id": "t-1"},
    )

    body = response.text
    assert 'event: error' in body or 'event: message' in body
    assert '智能助手暂时无法响应' in body or '系统暂时无法处理该请求' in body
```

- [ ] **Step 5: 运行测试，确认清洗和 SSE 降级全部通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api/test_chat_stream_api.py tests/test_guardrails/test_chat_output_filters.py -v`

Expected: PASS，且不会再把 `<tool_calls>` 原样吐给前端。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/api/chat.py \
  patient_agent_backend/app/chat/orchestrator.py \
  patient_agent_backend/app/chat/output_filters.py \
  patient_agent_backend/tests/test_api/test_chat_stream_api.py \
  patient_agent_backend/tests/test_guardrails/test_chat_output_filters.py
git commit -m "feat(chat): unify stream and response guardrails"
```

### Task 3: 增加线程级流程上下文，稳定挂号闭环

**Files:**
- Create: `patient_agent_backend/app/chat/flow_state.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Modify: `patient_agent_backend/app/tools/registration_tools.py`
- Modify: `patient_agent_backend/app/tools/doctor_tools.py`
- Test: `patient_agent_backend/tests/test_tools/test_registration_flow_state.py`
- Test: `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`

**Interfaces:**
- Consumes: `ChatOrchestrator`, `query_doctor_schedules`, `query_schedule_detail`, `create_registration`
- Produces: `FlowStateStore.load(thread_key: str) -> dict`, `FlowStateStore.save(thread_key: str, payload: dict) -> None`, `pending_registration_confirmation` 槽位

- [ ] **Step 1: 写失败测试，覆盖“待确认挂号”不允许跳步创建**

```python
async def test_create_registration_requires_pending_confirmation(flow_state_store, tools):
    await flow_state_store.save(
        "patient:9:thread-1",
        {"pending_registration_confirmation": None},
    )

    result = await tools["create_registration"].ainvoke(
        {
            "work_plan_id": 1,
            "doctor_schedule_id": 2,
            "doctor_id": 3,
            "dept_sub_id": 4,
            "appointment_date": "2026-06-26",
            "slot": 1,
        }
    )

    assert '"ok": false' in result
    assert "请先确认挂号信息" in result
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_tools/test_registration_flow_state.py -v`

Expected: FAIL，当前工具只校验登录患者，不校验线程级待确认状态。

- [ ] **Step 3: 写最小实现，增加线程级流程状态存储**

```python
from dataclasses import dataclass, field


@dataclass
class FlowState:
    intent: str | None = None
    selected_dept: dict | None = None
    selected_doctor: dict | None = None
    selected_date: str | None = None
    selected_work_plan_id: int | None = None
    selected_schedule_slot: dict | None = None
    pending_registration_confirmation: dict | None = None


class FlowStateStore:
    def __init__(self, redis_client):
        self._redis = redis_client

    async def load(self, thread_key: str) -> FlowState:
        raw = await self._redis.get(thread_key)
        if not raw:
            return FlowState()
        return FlowState(**json.loads(raw))

    async def save(self, thread_key: str, payload: FlowState) -> None:
        await self._redis.set(
            thread_key,
            json.dumps(payload.__dict__, ensure_ascii=False),
            ex=60 * 60 * 24,
        )
```

```python
if flow_state.pending_registration_confirmation is None:
    return err(
        "请先确认挂号信息",
        "请先向用户展示待确认挂号信息，收到明确确认后再创建挂号。",
    )
```

- [ ] **Step 4: 写失败测试，覆盖聊天闭环**

```python
def test_chat_registration_flow_requires_confirm_step(client):
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "帮我预约今天内科张医生的号", "thread_id": "flow-1"},
    )

    assert response.status_code == 200
    assert "请确认" in response.json()["message"]
```

- [ ] **Step 5: 运行测试，确认闭环与槽位更新通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_tools/test_registration_flow_state.py tests/test_integration/test_chat_registration_flow.py -v`

Expected: PASS，创建挂号前必须先命中待确认状态，集成测试能看到“请确认”。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/chat/flow_state.py \
  patient_agent_backend/app/chat/orchestrator.py \
  patient_agent_backend/app/tools/registration_tools.py \
  patient_agent_backend/app/tools/doctor_tools.py \
  patient_agent_backend/tests/test_tools/test_registration_flow_state.py \
  patient_agent_backend/tests/test_integration/test_chat_registration_flow.py
git commit -m "feat(chat): add thread flow state for registration"
```

### Task 4: 侧栏动作结构化，接入统一编排层

**Files:**
- Modify: `patient_agent_backend/app/api/patient.py`
- Modify: `patient_agent_backend/app/patient_sidebar/service.py`
- Create: `patient_agent_backend/app/patient_sidebar/actions.py`
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/App.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx`
- Test: `patient_agent_backend/tests/test_api/test_sidebar_action_api.py`

**Interfaces:**
- Consumes: `ChatOrchestrator.run_once()`, `ChatOrchestrator.run_stream()`, `PatientSidebarService.get_sidebar()`
- Produces: `POST /api/patient/sidebar/action`, request body `{"action":"confirm_registration","thread_id":"thread-9","payload":{"doctor_id":12,"department_name":"内科"}}`

- [ ] **Step 1: 写失败测试，锁定侧栏动作接口**

```python
def test_sidebar_action_uses_authenticated_patient(client):
    response = client.post(
        "/api/patient/sidebar/action",
        headers={"Authorization": "Bearer token-1"},
        json={
            "action": "confirm_registration",
            "thread_id": "thread-9",
            "payload": {"doctor_id": 12, "department_name": "内科"},
        },
    )

    assert response.status_code == 200
    assert response.json()["thread_id"] == "thread-9"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api/test_sidebar_action_api.py -v`

Expected: FAIL，当前不存在 `/api/patient/sidebar/action`。

- [ ] **Step 3: 写最小实现，增加结构化侧栏动作入口**

```python
@router.post("/sidebar/action")
async def sidebar_action(
    payload: SidebarActionRequest,
    session: PatientSession = Depends(require_patient_session),
):
    result = await get_chat_orchestrator().run_once(
        session=session,
        user_message=build_sidebar_action_message(payload),
        thread_id=payload.thread_id,
    )
    return result.__dict__
```

```javascript
sidebarAction(action, threadId, payload) {
  return api.post('/patient/sidebar/action', {
    action,
    thread_id: threadId,
    payload,
  })
}
```

- [ ] **Step 4: 改前端侧栏，不再直接拼自由文本**

```javascript
const handleConfirm = async () => {
  if (!activeDepartment || !confirmDoctor) return
  await patientApi.sidebarAction('confirm_registration', currentThreadId, {
    department_name: activeDepartment.departmentName,
    doctor_id: confirmDoctor.doctorId,
    doctor_name: confirmDoctor.doctorName,
  })
  setConfirmDoctor(null)
}
```

- [ ] **Step 5: 运行接口测试和前端构建**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api/test_sidebar_action_api.py -v`

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build`

Expected: pytest PASS；前端构建成功，无新的类型或语法错误。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/api/patient.py \
  patient_agent_backend/app/patient_sidebar/service.py \
  patient_agent_backend/app/patient_sidebar/actions.py \
  patient_agent_frontend/src/api/index.js \
  patient_agent_frontend/src/App.jsx \
  patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx \
  patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx \
  patient_agent_backend/tests/test_api/test_sidebar_action_api.py
git commit -m "feat(sidebar): route structured actions through orchestrator"
```

### Task 5: 补齐护栏、HMS client、工具层和聊天集成测试

**Files:**
- Create: `patient_agent_backend/tests/test_guardrails/test_input_guard.py`
- Create: `patient_agent_backend/tests/test_guardrails/test_output_guard.py`
- Create: `patient_agent_backend/tests/test_hms_client/test_client.py`
- Create: `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`
- Modify: `patient_agent_backend/tests/test_api/test_chat_auth.py`
- Modify: `patient_agent_backend/tests/test_hms_client/test_registration_service.py`
- Modify: `patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py`

**Interfaces:**
- Consumes: `check_input()`, `check_output()`, `HmsClient._request()`, `create_registration/query_registration/cancel_registration`
- Produces: 护栏测试、HMS client 401/timeout/4xx/5xx 测试、工具层闭环测试、聊天集成测试

- [ ] **Step 1: 写失败测试，覆盖输入护栏与免责声明**

```python
from app.guardrails.input_guard import check_input
from app.guardrails.output_guard import check_output


def test_check_input_blocks_diagnosis_request():
    result = check_input("请你帮我判断是不是肺炎")
    assert result.blocked is True
    assert result.reason == "diagnosis_request"


def test_check_output_appends_disclaimer_once():
    message, shown = check_output("建议你先休息。", needs_disclaimer=True, disclaimer_shown=False)
    assert "以上信息仅供参考" in message
    assert shown is True
```

- [ ] **Step 2: 写失败测试，覆盖 HMS client 重登与异常映射**

```python
async def test_request_retries_once_after_401(fake_transport):
    client = HmsClient(base_url="http://test", timeout=1)
    response = await client.post("/patient/selectByPage", json={"page": 1, "length": 20})
    assert response["code"] == 200
```

- [ ] **Step 3: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_guardrails tests/test_hms_client/test_client.py tests/test_tools/test_registration_flow_tools.py -v`

Expected: FAIL，当前 guardrails 测试文件不存在，`HmsClient` 相关异常路径未被覆盖。

- [ ] **Step 4: 写最小实现，只补缺口不做额外重构**

```python
import httpx
import pytest

from app.hms_client.client import HmsClient
from app.hms_client.exceptions import HmsTimeoutError


async def test_request_raises_timeout_error(monkeypatch):
    client = HmsClient(base_url="http://test", timeout=1)

    async def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(client._http, "request", raise_timeout)

    with pytest.raises(HmsTimeoutError):
        await client.post("/patient/selectByPage", json={"page": 1, "length": 20})
```

```python
def test_chat_history_uses_authenticated_patient_id():
    memory = FakeMemory()
    graph = FakeGraph()
    client = create_client(memory, graph, with_auth_override=True)

    response = client.get(
        "/api/chat/history",
        headers={"Authorization": "Bearer token-1"},
        params={"patient_id": 999, "thread_id": "t-2"},
    )

    assert response.status_code == 200
    assert memory.loaded[0][0] == 88


def test_chat_ignores_forwarded_patient_id():
    memory = FakeMemory()
    graph = FakeGraph()
    client = create_client(memory, graph, with_auth_override=True)

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "你好", "patient_id": 999, "thread_id": "t-1"},
    )

    assert response.status_code == 200
    assert graph.state["patient_id"] == 88
    assert memory.loaded[0][0] == 88
```

- [ ] **Step 5: 运行完整测试组**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_guardrails tests/test_hms_client tests/test_tools tests/test_api/test_chat_auth.py -v`

Expected: PASS，且四类测试都出现明确通过结果。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/tests/test_guardrails/test_input_guard.py \
  patient_agent_backend/tests/test_guardrails/test_output_guard.py \
  patient_agent_backend/tests/test_hms_client/test_client.py \
  patient_agent_backend/tests/test_tools/test_registration_flow_tools.py \
  patient_agent_backend/tests/test_api/test_chat_auth.py \
  patient_agent_backend/tests/test_hms_client/test_registration_service.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py
git commit -m "test(chat): cover guardrails hms client and tools"
```

### Task 6: 增加请求级日志与上下文透传

**Files:**
- Create: `patient_agent_backend/app/logging_utils.py`
- Create: `patient_agent_backend/app/middleware/request_context.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Modify: `patient_agent_backend/app/hms_client/client.py`
- Modify: `patient_agent_backend/app/tools/registration_tools.py`
- Test: `patient_agent_backend/tests/test_logging/test_request_context.py`

**Interfaces:**
- Consumes: FastAPI middleware, `logging.LoggerAdapter`, `ChatRunResult`
- Produces: `get_request_logger(name: str) -> logging.LoggerAdapter`, `request_id/patient_id/thread_id/guardrail_result/reply_type/tool_name/tool_status/hms_error_type/degraded` 结构化字段

- [ ] **Step 1: 写失败测试，覆盖 request_id 和 patient_id 注入**

```python
def test_request_context_logs_request_and_patient(caplog, client):
    with caplog.at_level("INFO"):
        client.post(
            "/api/chat",
            headers={"Authorization": "Bearer token-1"},
            json={"message": "查看我的挂号", "thread_id": "log-1"},
        )

    assert any("request_id" in record.message or hasattr(record, "request_id") for record in caplog.records)
    assert any(getattr(record, "patient_id", None) == 88 for record in caplog.records)
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_logging/test_request_context.py -v`

Expected: FAIL，当前没有 request context middleware，也没有结构化日志字段。

- [ ] **Step 3: 写最小实现，增加中间件与 logger adapter**

```python
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

```python
def log_chat_result(logger, *, request_id, patient_id, thread_id, guardrail_result, reply_type, degraded):
    logger.info(
        "chat_result",
        extra={
            "request_id": request_id,
            "patient_id": patient_id,
            "thread_id": thread_id,
            "guardrail_result": guardrail_result,
            "reply_type": reply_type,
            "degraded": degraded,
        },
    )
```

- [ ] **Step 4: 运行日志测试**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_logging/test_request_context.py -v`

Expected: PASS，日志里能捕获 `request_id`、`patient_id`，响应头带 `X-Request-ID`。

- [ ] **Step 5: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/logging_utils.py \
  patient_agent_backend/app/middleware/request_context.py \
  patient_agent_backend/app/main.py \
  patient_agent_backend/app/chat/orchestrator.py \
  patient_agent_backend/app/hms_client/client.py \
  patient_agent_backend/app/tools/registration_tools.py \
  patient_agent_backend/tests/test_logging/test_request_context.py
git commit -m "feat(logging): add request and patient context logs"
```

### Task 7: 收敛 Settings、环境变量与 CORS

**Files:**
- Modify: `patient_agent_backend/app/config/settings.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_backend/.env.example`
- Create: `patient_agent_backend/.env.development.example`
- Create: `patient_agent_backend/.env.test.example`
- Create: `patient_agent_backend/.env.production.example`
- Create: `patient_agent_backend/tests/test_config/test_settings.py`

**Interfaces:**
- Consumes: `Settings`
- Produces: `app_env`, `cors_allowed_origins`, `cors_allow_credentials`, `log_level`, `sms_return_code_dev`, 环境分层样例文件

- [ ] **Step 1: 写失败测试，锁定 CORS 与环境配置读取**

```python
from app.config.settings import Settings


def test_settings_parse_cors_origins_from_csv(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.example.com,https://b.example.com")

    settings = Settings()

    assert settings.app_env == "production"
    assert settings.cors_allowed_origins == [
        "https://a.example.com",
        "https://b.example.com",
    ]
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_config/test_settings.py -v`

Expected: FAIL，当前 `Settings` 没有 `app_env` 和 `cors_allowed_origins` 字段。

- [ ] **Step 3: 写最小实现，去掉硬编码 `*`**

```python
class Settings(BaseSettings):
    app_env: str = "development"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    cors_allow_credentials: bool = True
    log_level: str = "INFO"
    sms_return_code_dev: bool = True
```

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

- [ ] **Step 4: 补环境样例文件**

```dotenv
# .env.production.example
APP_ENV=production
CORS_ALLOWED_ORIGINS=https://patient.example.com
CORS_ALLOW_CREDENTIALS=true
LOG_LEVEL=INFO
SMS_RETURN_CODE_DEV=false
```

- [ ] **Step 5: 运行配置测试和健康检查测试**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_config/test_settings.py tests/test_api/test_chat_auth.py -v`

Expected: PASS，且 `main.py` 不再硬编码 `allow_origins=["*"]`。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/config/settings.py \
  patient_agent_backend/app/main.py \
  patient_agent_backend/.env.example \
  patient_agent_backend/.env.development.example \
  patient_agent_backend/.env.test.example \
  patient_agent_backend/.env.production.example \
  patient_agent_backend/tests/test_config/test_settings.py
git commit -m "feat(config): split env settings and tighten cors"
```

### Task 8: 端到端验证与收尾

**Files:**
- Modify: `patient_agent_backend/tests/test_api/test_chat_auth.py`
- Modify: `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`
- Modify: `patient_agent_frontend/src/App.jsx`
- Test: `patient_agent_backend/tests/test_guardrails/test_input_guard.py`
- Test: `patient_agent_backend/tests/test_guardrails/test_output_guard.py`
- Test: `patient_agent_backend/tests/test_hms_client/test_client.py`
- Test: `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`
- Test: `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`

**Interfaces:**
- Consumes: 所有前序任务产出的 orchestrator、flow state、sidebar action、logging、settings
- Produces: 第一阶段完整回归基线与第二阶段基础工程化验收结果

- [ ] **Step 1: 运行后端完整关键测试集**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && PYTHONPATH=. ../.venv-py312/bin/pytest tests/test_api tests/test_guardrails tests/test_hms_client tests/test_tools tests/test_integration tests/test_logging tests/test_config -v`

Expected: PASS，且不再出现聊天主流程、护栏、HMS client、工具层的红灯。

- [ ] **Step 2: 运行前端构建**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build`

Expected: PASS，Vite 构建完成，无新增构建错误。

- [ ] **Step 3: 运行本地全栈手工回归**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && docker compose up -d --build`

Expected:
- 患者登录成功
- “查科室 -> 查医生 -> 查排班 -> 确认挂号 -> 查询/取消挂号” 能走通
- `/api/chat` 与 `/api/chat/stream` 对同一输入返回同类护栏/免责声明/转人工结论
- HMS、Redis、LLM 失败时不再直接裸 500

- [ ] **Step 4: 提交最终整合**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend patient_agent_frontend
git commit -m "feat(agent): harden orchestration safety and registration flow"
```
