# Patient Agent P0/P1 稳定性改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `patient_agent_backend` 增加 Redis 持久化的 `FlowState`、高频强流程前置路由、工具运行时抽象以及最小必要错误分级与日志，稳定挂号确认主链路。

**Architecture:** 保留现有 `LangGraph` 主结构与工具签名，在图执行前增加轻量前置路由，在图执行中抽出工具运行时辅助层，并将线程级 `FlowState` 从进程内内存迁移到 Redis。测试继续以单测和轻量集成为主，避免改动前端协议。

**Tech Stack:** Python 3.11、FastAPI、LangChain/LangGraph、redis.asyncio、pytest

## Global Constraints

- 保留现有 `FlowState` 字段结构，不重写整个 `LangGraph` 图结构。
- 不把全部聊天请求改为规则引擎或状态机，只拦截高确定性高频意图。
- 不调整前端 `tool_start` / `tool_end` SSE 协议。
- 不修改现有工具函数签名。
- 默认 `FlowState` 使用 Redis 持久化，测试仍可显式注入 `InMemoryFlowStateStore`。
- `FlowState` Redis key 使用 `chat:flow-state:{patient_id}:{thread_id}`。
- `FlowState` TTL 使用 24 小时。
- 前置路由仅覆盖 `query_registration`、取消挂号前置路径、存在 `pending_registration_confirmation` 的挂号确认路径。

---

### Task 1: 抽象并实现 Redis FlowState Store

**Files:**
- Modify: `patient_agent_backend/app/chat/flow_state.py`
- Modify: `patient_agent_backend/app/config/settings.py`
- Test: `patient_agent_backend/tests/test_memory/test_flow_state_store.py`

**Interfaces:**
- Consumes: `redis.asyncio.Redis`
- Produces: `class FlowStateStore`, `class RedisFlowStateStore`, `get_flow_state_store() -> FlowStateStore`

- [ ] **Step 1: 写失败测试，定义 Redis store 的期望行为**

```python
import pytest

from app.chat.flow_state import FlowState, RedisFlowStateStore


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expiry = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value
        self.expiry[key] = ex

    async def delete(self, key):
        self.data.pop(key, None)
        self.expiry.pop(key, None)


@pytest.mark.asyncio
async def test_redis_flow_state_store_round_trip():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)

    await store.save("patient:8:thread-1", {"pending_registration_confirmation": {"work_plan_id": 11}})
    result = await store.load("patient:8:thread-1")

    assert isinstance(result, FlowState)
    assert result.pending_registration_confirmation == {"work_plan_id": 11}
    assert redis.expiry["chat:flow-state:8:thread-1"] == 60


@pytest.mark.asyncio
async def test_redis_flow_state_store_returns_empty_state_for_missing_key():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)

    result = await store.load("patient:8:missing")

    assert result == FlowState()
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_memory/test_flow_state_store.py -v`
Expected: FAIL，提示 `RedisFlowStateStore` 或 `FlowStateStore` 未定义。

- [ ] **Step 3: 进行最小实现**

```python
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class FlowState:
    intent: str | None = None
    selected_dept: dict | None = None
    selected_doctor: dict | None = None
    selected_date: str | None = None
    selected_work_plan_id: int | None = None
    selected_schedule_slot: dict | None = None
    pending_registration_confirmation: dict | None = None
    schedule_candidates_by_work_plan: dict[int, dict] | None = None


class FlowStateStore(ABC):
    @abstractmethod
    async def load(self, thread_key: str) -> FlowState: ...

    @abstractmethod
    async def save(self, thread_key: str, payload: dict | FlowState) -> None: ...

    @abstractmethod
    async def delete(self, thread_key: str) -> None: ...


class RedisFlowStateStore(FlowStateStore):
    def __init__(self, redis_client, ttl_seconds: int = 86400):
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    def _redis_key(self, thread_key: str) -> str:
        _, patient_id, thread_id = thread_key.split(":", 2)
        return f"chat:flow-state:{patient_id}:{thread_id}"

    async def load(self, thread_key: str) -> FlowState:
        raw = await self._redis.get(self._redis_key(thread_key))
        if not raw:
            return FlowState()
        return FlowState(**json.loads(raw))

    async def save(self, thread_key: str, payload: dict | FlowState) -> None:
        state = payload if isinstance(payload, FlowState) else FlowState(**payload)
        await self._redis.set(
            self._redis_key(thread_key),
            json.dumps(asdict(state), ensure_ascii=False),
            ex=self._ttl_seconds,
        )

    async def delete(self, thread_key: str) -> None:
        await self._redis.delete(self._redis_key(thread_key))
```

- [ ] **Step 4: 补齐配置项与 getter/setter 兼容**

```python
class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/1"
    flow_state_ttl_seconds: int = 60 * 60 * 24
```

```python
_flow_state_store: FlowStateStore | None = None


def set_flow_state_store(store: FlowStateStore | None) -> None:
    global _flow_state_store
    _flow_state_store = store


def get_flow_state_store() -> FlowStateStore:
    global _flow_state_store
    if _flow_state_store is None:
        _flow_state_store = InMemoryFlowStateStore()
    return _flow_state_store
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_memory/test_flow_state_store.py -v`
Expected: PASS，2 个新增测试通过。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/chat/flow_state.py patient_agent_backend/app/config/settings.py patient_agent_backend/tests/test_memory/test_flow_state_store.py
git commit -m "feat(patient-agent): persist flow state in redis"
```

### Task 2: 在应用启动时注入 Redis FlowState Store

**Files:**
- Modify: `patient_agent_backend/app/main.py`
- Test: `patient_agent_backend/tests/test_api/test_main_flow_state_store.py`

**Interfaces:**
- Consumes: `RedisFlowStateStore(redis_client, ttl_seconds=settings.flow_state_ttl_seconds)`
- Produces: 应用启动时默认将 `get_flow_state_store()` 指向 Redis 实现

- [ ] **Step 1: 写失败测试，约束启动时的 store 注入**

```python
from app.chat.flow_state import RedisFlowStateStore


def test_main_initializes_redis_flow_state_store(monkeypatch):
    created = {}

    class FakeRedisClient:
        pass

    def fake_set_flow_state_store(store):
        created["store"] = store

    monkeypatch.setattr("app.main.set_flow_state_store", fake_set_flow_state_store)
    store = RedisFlowStateStore(FakeRedisClient(), ttl_seconds=10)

    assert isinstance(store, RedisFlowStateStore)
```

- [ ] **Step 2: 运行测试，确认当前缺少初始化路径**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_main_flow_state_store.py -v`
Expected: FAIL，测试无法证明启动期进行了 `set_flow_state_store(...)` 注入。

- [ ] **Step 3: 在 `main.py` 中注入 Redis FlowState Store**

```python
from app.chat.flow_state import RedisFlowStateStore, set_flow_state_store


redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
app.state.redis = redis_client

flow_state_store = RedisFlowStateStore(
    redis_client,
    ttl_seconds=settings.flow_state_ttl_seconds,
)
set_flow_state_store(flow_state_store)
logger.info("FlowState store 初始化完成")
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_main_flow_state_store.py -v`
Expected: PASS，能够验证启动路径会创建并注入 Redis store。

- [ ] **Step 5: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/main.py patient_agent_backend/tests/test_api/test_main_flow_state_store.py
git commit -m "feat(patient-agent): initialize redis flow state store"
```

### Task 3: 增加高频意图前置路由

**Files:**
- Create: `patient_agent_backend/app/chat/pre_router.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Test: `patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py`

**Interfaces:**
- Consumes: `get_flow_state_store()`, `ALL_TOOLS`, `PatientSession`, `thread_id`, `user_message`
- Produces: `async def try_pre_route(*, session, thread_id: str, user_message: str) -> ChatRunResult | None`

- [ ] **Step 1: 写失败测试，先定义三类命中场景**

```python
import pytest

from app.chat.flow_state import InMemoryFlowStateStore, set_flow_state_store
from app.chat.pre_router import try_pre_route


@pytest.mark.asyncio
async def test_pre_router_routes_query_registration():
    set_flow_state_store(InMemoryFlowStateStore())
    session = type("Session", (), {"patient_id": 8})()

    result = await try_pre_route(
        session=session,
        thread_id="thread-1",
        user_message="我的挂号",
    )

    assert result is not None
    assert result.reply_type == "pre_route"


@pytest.mark.asyncio
async def test_pre_router_routes_confirmation_when_pending_state_exists():
    store = InMemoryFlowStateStore()
    set_flow_state_store(store)
    await store.save("patient:8:thread-2", {"pending_registration_confirmation": {"work_plan_id": 11}})
    session = type("Session", (), {"patient_id": 8})()

    result = await try_pre_route(
        session=session,
        thread_id="thread-2",
        user_message="确认",
    )

    assert result is not None
    assert result.reply_type == "pre_route"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_chat_orchestrator_pre_router.py -v`
Expected: FAIL，`pre_router.py` 或 `try_pre_route()` 不存在。

- [ ] **Step 3: 写最小路由实现**

```python
import re

from app.chat.flow_state import get_flow_state_store
from app.chat.models import ChatRunResult


QUERY_REGISTRATION_PATTERNS = ("我的挂号", "挂号记录", "我挂了哪些号")
CANCEL_PATTERNS = ("取消挂号", "退号", "取消这个预约")
CONFIRM_PATTERNS = ("确认", "就这个", "帮我预约这个")


async def try_pre_route(*, session, thread_id: str, user_message: str):
    text = (user_message or "").strip()
    state = await get_flow_state_store().load(f"patient:{session.patient_id}:{thread_id}")

    if any(keyword in text for keyword in QUERY_REGISTRATION_PATTERNS):
        return ChatRunResult(thread_id=thread_id, message="PRE_ROUTE_QUERY_REGISTRATION", reply_type="pre_route", needs_handoff=False, disclaimer_added=False, guardrail_result=None, degraded=False)

    if any(keyword in text for keyword in CANCEL_PATTERNS):
        return ChatRunResult(thread_id=thread_id, message="PRE_ROUTE_CANCEL_REGISTRATION", reply_type="pre_route", needs_handoff=False, disclaimer_added=False, guardrail_result=None, degraded=False)

    if state.pending_registration_confirmation and (any(keyword in text for keyword in CONFIRM_PATTERNS) or re.search(r"第\s*\d+\s*个", text)):
        return ChatRunResult(thread_id=thread_id, message="PRE_ROUTE_CREATE_REGISTRATION", reply_type="pre_route", needs_handoff=False, disclaimer_added=False, guardrail_result=None, degraded=False)

    return None
```

- [ ] **Step 4: 在 `orchestrator.py` 中接入前置路由**

```python
from app.chat.pre_router import try_pre_route


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
    return pre_routed
```

- [ ] **Step 5: 用真实工具替换占位 message**

```python
async def _invoke_tool(tool_name: str, args: dict) -> str:
    tool = next(tool for tool in ALL_TOOLS if tool.name == tool_name)
    return await tool.ainvoke(args)
```

```python
if any(keyword in text for keyword in QUERY_REGISTRATION_PATTERNS):
    tool_result = await _invoke_tool("query_registration", {})
    return ChatRunResult(thread_id=thread_id, message=tool_result, reply_type="pre_route", needs_handoff=False, disclaimer_added=False, guardrail_result=None, degraded=False)
```

- [ ] **Step 6: 运行测试，确认通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_chat_orchestrator_pre_router.py -v`
Expected: PASS，三类前置路由命中与未命中场景通过。

- [ ] **Step 7: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/chat/pre_router.py patient_agent_backend/app/chat/orchestrator.py patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py
git commit -m "feat(patient-agent): add pre-routing for critical intents"
```

### Task 4: 抽出工具运行时辅助层

**Files:**
- Create: `patient_agent_backend/app/agent/tool_runtime.py`
- Modify: `patient_agent_backend/app/agent/nodes.py`
- Test: `patient_agent_backend/tests/test_agent/test_tool_runtime.py`

**Interfaces:**
- Consumes: `AIMessage`, `HumanMessage`, `tools: list`, `last_user_content: str`
- Produces: `async def run_tool_rounds(llm, llm_messages: list, response: AIMessage, tools: list, last_user_content: str) -> AIMessage`

- [ ] **Step 1: 写失败测试，冻结当前关键行为**

```python
import pytest

from langchain_core.messages import AIMessage

from app.agent.tool_runtime import normalize_tool_calls


def test_normalize_tool_calls_recovers_empty_tool_name():
    calls = [{"id": "1", "name": "", "args": {}}]

    normalized = normalize_tool_calls(calls, "我的挂号")

    assert normalized[0]["name"] == "query_registration"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_agent/test_tool_runtime.py -v`
Expected: FAIL，`tool_runtime.py` 和 `normalize_tool_calls` 不存在。

- [ ] **Step 3: 提取归一化与结果解析逻辑**

```python
import json


def normalize_tool_calls(tool_calls: list[dict], last_user_content: str) -> list[dict]:
    normalized = []
    for tool_call in tool_calls:
        if tool_call.get("name"):
            normalized.append(tool_call)
            continue
        recovered = recover_tool_call(last_user_content)
        if recovered:
            normalized.append({**tool_call, **recovered})
    return normalized


def classify_tool_result(tool_result_str: str) -> str:
    parsed = json.loads(tool_result_str)
    if parsed.get("ok") is False:
        return "validation_error" if "参数" in parsed.get("error", "") else "upstream_error"
    if parsed.get("data") in ([], {}, None):
        return "empty_result"
    return "ok"
```

- [ ] **Step 4: 提取多轮工具执行函数**

```python
async def run_tool_rounds(llm, llm_messages: list, response, tools: list, last_user_content: str):
    tool_rounds = 0
    tool_map = {tool.name: tool for tool in tools}

    while isinstance(response, AIMessage) and response.tool_calls:
        tool_rounds += 1
        if tool_rounds > 5:
            return AIMessage(content="系统暂时无法处理该请求，请稍后再试。")

        for tool_call in normalize_tool_calls(response.tool_calls, last_user_content):
            tool_name = tool_call["name"]
            tool_result = await tool_map[tool_name].ainvoke(tool_call["args"])
            llm_messages.append(AIMessage(content="", tool_calls=[tool_call]))
            llm_messages.append(HumanMessage(content=f"工具 {tool_name} 返回结果：\n{tool_result}"))
            llm_messages.append(HumanMessage(content="【重要提醒】请基于以上工具返回的真实数据继续处理用户请求。"))
        response = await llm.ainvoke(llm_messages)

    return response
```

- [ ] **Step 5: 在 `nodes.py` 中替换内联逻辑**

```python
from app.agent.tool_runtime import run_tool_rounds


response = await llm.ainvoke(llm_messages)
response = await run_tool_rounds(
    llm=llm,
    llm_messages=llm_messages,
    response=response,
    tools=tools,
    last_user_content=last_user_content,
)
return {"messages": [response]}
```

- [ ] **Step 6: 运行测试，确认通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_agent/test_tool_runtime.py tests/test_agent/test_multi_tool_loop.py tests/test_agent/test_tool_fallback.py -v`
Expected: PASS，工具回退、多轮调用和运行时抽象测试全部通过。

- [ ] **Step 7: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/agent/tool_runtime.py patient_agent_backend/app/agent/nodes.py patient_agent_backend/tests/test_agent/test_tool_runtime.py
git commit -m "refactor(patient-agent): extract tool runtime loop"
```

### Task 5: 增加错误分级和关键日志

**Files:**
- Modify: `patient_agent_backend/app/agent/tool_runtime.py`
- Modify: `patient_agent_backend/app/chat/pre_router.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Test: `patient_agent_backend/tests/test_logging/test_patient_agent_route_logging.py`

**Interfaces:**
- Consumes: `logger.info(...)`, `classify_tool_result(tool_result_str: str) -> str`
- Produces: `error_type`, `route_type`, `degraded` 等结构化日志字段

- [ ] **Step 1: 写失败测试，验证关键日志字段存在**

```python
def test_pre_route_logs_route_type(caplog):
    logger = logging.getLogger("app.chat.pre_router")

    logger.info("pre_route_hit", extra={"route_type": "pre_route", "degraded": False})

    assert "pre_route" in caplog.text
```

- [ ] **Step 2: 运行测试，确认当前缺少约束**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_logging/test_patient_agent_route_logging.py -v`
Expected: FAIL，测试文件不存在或尚未记录对应字段。

- [ ] **Step 3: 在前置路由和工具运行时增加日志**

```python
logger.info(
    "pre_route_hit",
    extra={
        "route_type": "pre_route",
        "patient_id": session.patient_id,
        "thread_id": thread_id,
        "tool_name": "query_registration",
        "tool_status": "success",
        "degraded": False,
    },
)
```

```python
logger.info(
    "tool_call_end",
    extra={
        "tool_name": tool_name,
        "tool_status": "success",
        "error_type": classify_tool_result(tool_result_str),
        "route_type": "graph_route",
        "degraded": False,
    },
)
```

- [ ] **Step 4: 在异常路径补齐 `error_type`**

```python
logger.error(
    "tool_call_end",
    extra={
        "tool_name": tool_name,
        "tool_status": "error",
        "error_type": "runtime_error",
        "route_type": "graph_route",
        "degraded": True,
    },
)
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_logging/test_patient_agent_route_logging.py -v`
Expected: PASS，日志包含 `route_type`、`error_type`、`degraded`。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/app/agent/tool_runtime.py patient_agent_backend/app/chat/pre_router.py patient_agent_backend/app/chat/orchestrator.py patient_agent_backend/tests/test_logging/test_patient_agent_route_logging.py
git commit -m "feat(patient-agent): add route and error logging"
```

### Task 6: 回归挂号主链路并完成验证

**Files:**
- Modify: `patient_agent_backend/tests/test_tools/test_registration_flow_state.py`
- Modify: `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`
- Modify: `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`
- Modify: `patient_agent_backend/tests/test_api/test_chat_orchestrator.py`

**Interfaces:**
- Consumes: `RedisFlowStateStore`, `try_pre_route(...)`, `run_tool_rounds(...)`
- Produces: 回归证明：Redis store、前置路由、挂号确认链路可共同工作

- [ ] **Step 1: 补写 Redis store 下的挂号确认态测试**

```python
@pytest.mark.asyncio
async def test_create_registration_reads_pending_confirmation_from_redis_store():
    redis = FakeRedis()
    store = RedisFlowStateStore(redis, ttl_seconds=60)
    set_flow_state_store(store)
    await store.save(
        "patient:9:thread-2",
        {"pending_registration_confirmation": {"work_plan_id": 11, "doctor_schedule_id": 23, "doctor_id": 33, "dept_sub_id": 44, "appointment_date": "2026-06-28"}},
    )
```

- [ ] **Step 2: 补写前置路由与 orchestrator 集成测试**

```python
@pytest.mark.asyncio
async def test_run_once_uses_pre_router_before_graph(monkeypatch):
    orchestrator = ChatOrchestrator(memory=FakeMemory(), graph_factory=lambda: FakeGraph())
    monkeypatch.setattr("app.chat.orchestrator.try_pre_route", AsyncMock(return_value=ChatRunResult(thread_id="t-1", message="ok", reply_type="pre_route", needs_handoff=False, disclaimer_added=False, guardrail_result=None, degraded=False)))

    result = await orchestrator.run_once(session=FakeSession(), user_message="我的挂号", thread_id="t-1")

    assert result.reply_type == "pre_route"
```

- [ ] **Step 3: 运行受影响测试，确认全部通过**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_tools/test_registration_flow_state.py tests/test_tools/test_registration_flow_tools.py tests/test_integration/test_chat_registration_flow.py tests/test_api/test_chat_orchestrator.py -v`
Expected: PASS，挂号主链路相关回归全部通过。

- [ ] **Step 4: 运行扩展验证集合**

Run: `cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_agent tests/test_api tests/test_tools tests/test_integration tests/test_memory tests/test_logging -v`
Expected: PASS，受影响测试目录全部通过。

- [ ] **Step 5: 检查诊断与格式问题**

Run: 使用诊断工具检查最近修改文件的告警与错误。
Expected: 无新增语法错误、导入错误或明显 lint 问题。

- [ ] **Step 6: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system
git add patient_agent_backend/tests/test_tools/test_registration_flow_state.py patient_agent_backend/tests/test_tools/test_registration_flow_tools.py patient_agent_backend/tests/test_integration/test_chat_registration_flow.py patient_agent_backend/tests/test_api/test_chat_orchestrator.py
git commit -m "test(patient-agent): cover redis flow state and pre-routing"
```
