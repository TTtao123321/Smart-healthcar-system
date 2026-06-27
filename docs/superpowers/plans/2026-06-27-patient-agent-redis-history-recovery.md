# Patient Agent Redis History Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让患者在浏览器本地缓存 1 天后过期时，仍能从 Redis 恢复自己全部历史会话列表，并在恢复后回填浏览器缓存。

**Architecture:** 在 `patient_agent_backend` 的 Redis 记忆层之上新增“患者线程索引 + 线程摘要”两层数据模型，新增 `GET /api/chat/threads` 和可选删除接口，保持正文仍按 `chat:memory:{patient_id}:{thread_id}` 存储。前端继续采用“本地优先、后端兜底”的模式：本地线程列表有效时直接用本地，本地为空或过期时从 Redis 恢复线程列表，再按需懒加载正文并回填患者隔离缓存。

**Tech Stack:** FastAPI、redis.asyncio、Pydantic、pytest、React 19、Axios、Vitest、Testing Library

## Global Constraints

- 保留现有正文 Redis key `chat:memory:{patient_id}:{thread_id}`，不改消息正文结构。
- 新增患者级线程索引必须按 `patient_id` 隔离，且前端不允许自行传入 `patient_id`。
- 历史线程列表接口必须依赖当前登录 session，禁止跨患者读取。
- 正文、线程索引、线程摘要的 TTL 统一为 7 天。
- 前端恢复成功后必须重新写入浏览器缓存，并重置本地 1 天 TTL。
- 前端继续保持“线程列表恢复、正文懒加载”，禁止登录时一次性拉取全部历史正文。
- 旧 Redis 中无索引的历史正文不做扫描兼容恢复。

---

## File Structure

- Modify: `patient_agent_backend/app/memory/redis_memory.py`
  - 新增线程索引、线程摘要、列线程、删线程能力。
- Modify: `patient_agent_backend/app/api/chat.py`
  - 新增 `GET /api/chat/threads`，可选新增 `DELETE /api/chat/threads/{thread_id}`。
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
  - 保存正文时同步维护线程索引与摘要。
- Create: `patient_agent_backend/tests/test_memory/test_redis_memory_threads.py`
  - 覆盖 RedisMemory 线程索引和摘要行为。
- Create: `patient_agent_backend/tests/test_api/test_chat_threads_api.py`
  - 覆盖线程列表接口与删除接口的患者隔离。
- Modify: `patient_agent_frontend/src/api/index.js`
  - 新增 `chatApi.getThreads()`，可选 `chatApi.deleteThread()`。
- Modify: `patient_agent_frontend/src/App.jsx`
  - 本地线程缓存为空/过期时从后端恢复线程列表，回填本地缓存。
- Modify: `patient_agent_frontend/src/storage/patientCache.js`
  - 支持恢复后的线程列表、消息映射写回，必要时补充删除辅助函数。
- Create: `patient_agent_frontend/src/storage/patientHistoryRecovery.test.js`
  - 覆盖“本地失效 -> Redis 恢复 -> 回填本地缓存”流程。

### Task 1: 扩展 RedisMemory，支持线程索引和摘要

**Files:**
- Modify: `patient_agent_backend/app/memory/redis_memory.py`
- Create: `patient_agent_backend/tests/test_memory/test_redis_memory_threads.py`

**Interfaces:**
- Consumes:
  - `RedisMemory.save_messages(patient_id: str, thread_id: str, messages: list[dict]) -> None`
- Produces:
  - `RedisMemory.save_thread_snapshot(patient_id: str, thread_id: str, messages: list[dict]) -> None`
  - `RedisMemory.list_threads(patient_id: str, limit: int | None = None) -> list[dict]`
  - `RedisMemory.delete_thread(patient_id: str, thread_id: str) -> None`
  - `RedisMemory._threads_key(patient_id: str) -> str`
  - `RedisMemory._thread_meta_key(patient_id: str, thread_id: str) -> str`

- [ ] **Step 1: 写失败测试，锁定 Redis 线程索引行为**

```python
from app.memory.redis_memory import RedisMemory


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.hashes = {}
        self.sorted_sets = {}
        self.expires = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.expires[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def hset(self, key, mapping):
        self.hashes[key] = dict(mapping)

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def zadd(self, key, mapping):
        self.sorted_sets.setdefault(key, {})
        self.sorted_sets[key].update(mapping)

    async def zrevrange(self, key, start, end):
        items = self.sorted_sets.get(key, {})
        ordered = sorted(items.items(), key=lambda item: item[1], reverse=True)
        names = [name for name, _ in ordered]
        return names[start : end + 1 if end != -1 else None]

    async def expire(self, key, ttl):
        self.expires[key] = ttl

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.hashes.pop(key, None)
            self.sorted_sets.pop(key, None)
            self.expires.pop(key, None)

    async def zrem(self, key, member):
        if key in self.sorted_sets:
            self.sorted_sets[key].pop(member, None)


async def test_save_thread_snapshot_updates_thread_index_and_meta():
    memory = RedisMemory("redis://unused")
    memory._redis = FakeRedis()

    messages = [
        {"role": "user", "content": "我想挂号心内科"},
        {"role": "assistant", "content": "已为您找到今日可预约医生。"},
    ]

    await memory.save_messages("1", "thread-1", messages)
    await memory.save_thread_snapshot("1", "thread-1", messages)

    threads = await memory.list_threads("1")
    assert threads == [
        {
            "thread_id": "thread-1",
            "title": "我想挂号心内科",
            "last_message": "已为您找到今日可预约医生。",
            "message_count": 2,
        }
    ]


async def test_delete_thread_removes_body_meta_and_index():
    memory = RedisMemory("redis://unused")
    memory._redis = FakeRedis()
    messages = [{"role": "user", "content": "查询挂号记录"}]

    await memory.save_messages("1", "thread-1", messages)
    await memory.save_thread_snapshot("1", "thread-1", messages)
    await memory.delete_thread("1", "thread-1")

    assert await memory.load_messages("1", "thread-1") == []
    assert await memory.list_threads("1") == []
```

- [ ] **Step 2: 运行测试，确认新增接口尚不存在**

Run: `pytest patient_agent_backend/tests/test_memory/test_redis_memory_threads.py -q`

Expected: FAIL，报错包含 `AttributeError: 'RedisMemory' object has no attribute 'save_thread_snapshot'`。

- [ ] **Step 3: 在 `redis_memory.py` 中写最小实现**

```python
from datetime import datetime


class RedisMemory:
    _threads_prefix = "chat:threads:"
    _thread_meta_prefix = "chat:threadmeta:"
    _ttl_seconds = 86400 * 7

    def _threads_key(self, patient_id: str) -> str:
        return f"{self._threads_prefix}{patient_id}"

    def _thread_meta_key(self, patient_id: str, thread_id: str) -> str:
        return f"{self._thread_meta_prefix}{patient_id}:{thread_id}"

    @staticmethod
    def _build_thread_title(messages: list[dict]) -> str:
        first_user = next((item["content"] for item in messages if item.get("role") == "user" and item.get("content")), "")
        return first_user[:12] + ("..." if len(first_user) > 12 else "")

    @staticmethod
    def _build_last_message(messages: list[dict]) -> str:
        for item in reversed(messages):
            if item.get("content"):
                return str(item["content"])[:30]
        return ""

    async def save_thread_snapshot(self, patient_id: str, thread_id: str, messages: list[dict]) -> None:
        if not self._redis:
            return

        now_ts = int(datetime.now().timestamp())
        meta_key = self._thread_meta_key(patient_id, thread_id)
        threads_key = self._threads_key(patient_id)
        mapping = {
            "thread_id": thread_id,
            "title": self._build_thread_title(messages) or "新对话",
            "last_message": self._build_last_message(messages),
            "updated_at": datetime.now().isoformat(),
            "message_count": str(len(messages)),
        }
        await self._redis.hset(meta_key, mapping=mapping)
        await self._redis.zadd(threads_key, {thread_id: now_ts})
        await self._redis.expire(meta_key, self._ttl_seconds)
        await self._redis.expire(threads_key, self._ttl_seconds)

    async def list_threads(self, patient_id: str, limit: int | None = None) -> list[dict]:
        if not self._redis:
            return []

        end = -1 if limit is None else max(limit - 1, 0)
        thread_ids = await self._redis.zrevrange(self._threads_key(patient_id), 0, end)
        result = []
        for thread_id in thread_ids:
            meta = await self._redis.hgetall(self._thread_meta_key(patient_id, thread_id))
            if meta:
                result.append(
                    {
                        "thread_id": meta["thread_id"],
                        "title": meta.get("title", "新对话"),
                        "last_message": meta.get("last_message", ""),
                        "updated_at": meta.get("updated_at", ""),
                        "message_count": int(meta.get("message_count", 0)),
                    }
                )
        return result

    async def delete_thread(self, patient_id: str, thread_id: str) -> None:
        if not self._redis:
            return

        await self._redis.delete(
            self._key(patient_id, thread_id),
            self._thread_meta_key(patient_id, thread_id),
        )
        await self._redis.zrem(self._threads_key(patient_id), thread_id)
```

- [ ] **Step 4: 让正文保存时顺手刷新正文 TTL 常量**

```python
await self._redis.set(key, json.dumps(messages, ensure_ascii=False), ex=self._ttl_seconds)
```

- [ ] **Step 5: 运行测试，确认 RedisMemory 通过**

Run: `pytest patient_agent_backend/tests/test_memory/test_redis_memory_threads.py -q`

Expected: PASS，显示 `2 passed`。

- [ ] **Step 6: 提交 RedisMemory 改造**

```bash
git add patient_agent_backend/app/memory/redis_memory.py patient_agent_backend/tests/test_memory/test_redis_memory_threads.py
git commit -m "feat: add redis chat thread index"
```

### Task 2: 新增历史会话列表与删除接口

**Files:**
- Modify: `patient_agent_backend/app/api/chat.py`
- Modify: `patient_agent_backend/tests/test_api/test_chat_auth.py`
- Create: `patient_agent_backend/tests/test_api/test_chat_threads_api.py`

**Interfaces:**
- Consumes:
  - `RedisMemory.list_threads(patient_id: str, limit: int | None = None) -> list[dict]`
  - `RedisMemory.delete_thread(patient_id: str, thread_id: str) -> None`
- Produces:
  - `GET /api/chat/threads`
  - `DELETE /api/chat/threads/{thread_id}`

- [ ] **Step 1: 写失败测试，锁定患者线程列表接口**

```python
from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import set_auth_service_getter
from app.api.chat import set_memory


class FakeAuthService:
    async def get_session(self, token: str):
        return type("Session", (), {"patient_id": 1, "token": token})()


class FakeMemory:
    async def list_threads(self, patient_id: int, limit=None):
        assert patient_id == 1
        return [
            {
                "thread_id": "thread-1",
                "title": "我想挂号心内科",
                "last_message": "已为您找到今日可预约医生。",
                "updated_at": "2026-06-27T14:00:00",
                "message_count": 2,
            }
        ]

    async def delete_thread(self, patient_id: int, thread_id: str):
        assert patient_id == 1
        assert thread_id == "thread-1"


def test_chat_threads_returns_authenticated_patient_threads():
    set_auth_service_getter(lambda: FakeAuthService())
    set_memory(FakeMemory())
    client = TestClient(app)

    response = client.get("/api/chat/threads", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["threads"][0]["thread_id"] == "thread-1"


def test_delete_thread_uses_authenticated_patient_id():
    set_auth_service_getter(lambda: FakeAuthService())
    set_memory(FakeMemory())
    client = TestClient(app)

    response = client.delete("/api/chat/threads/thread-1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
```

- [ ] **Step 2: 运行测试，确认接口尚不存在**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_threads_api.py -q`

Expected: FAIL，状态码为 `404` 或路由缺失。

- [ ] **Step 3: 在 `chat.py` 中添加线程列表与删除接口**

```python
@router.get("/threads")
async def chat_threads(session: PatientSession = Depends(require_patient_session)):
    memory = get_memory()
    threads = await memory.list_threads(session.patient_id)
    return {"threads": threads}


@router.delete("/threads/{thread_id}")
async def delete_chat_thread(
    thread_id: str,
    session: PatientSession = Depends(require_patient_session),
):
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id 不能为空")

    memory = get_memory()
    await memory.delete_thread(session.patient_id, thread_id)
    return {"ok": True}
```

- [ ] **Step 4: 增加现有鉴权回归断言**

```python
def test_chat_threads_requires_login(client: TestClient):
    response = client.get("/api/chat/threads")
    assert response.status_code == 401
```

- [ ] **Step 5: 运行 API 测试，确认接口通过**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_threads_api.py patient_agent_backend/tests/test_api/test_chat_auth.py -q`

Expected: PASS，线程列表与鉴权测试均通过。

- [ ] **Step 6: 提交 API 改造**

```bash
git add patient_agent_backend/app/api/chat.py patient_agent_backend/tests/test_api/test_chat_threads_api.py patient_agent_backend/tests/test_api/test_chat_auth.py
git commit -m "feat: add chat thread recovery api"
```

### Task 3: 保存正文时同步维护线程摘要与索引

**Files:**
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Modify: `patient_agent_backend/tests/test_api/test_chat_orchestrator.py`

**Interfaces:**
- Consumes:
  - `RedisMemory.save_messages(patient_id, thread_id, messages) -> None`
  - `RedisMemory.save_thread_snapshot(patient_id, thread_id, messages) -> None`
- Produces:
  - 每次保存正文都会同步刷新线程索引和摘要

- [ ] **Step 1: 写失败测试，锁定 orchestrator 必须同步刷新线程索引**

```python
import pytest

from app.chat.orchestrator import ChatOrchestrator


class RecordingMemory:
    def __init__(self):
        self.saved_messages = None
        self.saved_snapshot = None

    async def load_messages(self, patient_id, thread_id):
        return []

    async def save_messages(self, patient_id, thread_id, messages):
        self.saved_messages = (patient_id, thread_id, list(messages))

    async def save_thread_snapshot(self, patient_id, thread_id, messages):
        self.saved_snapshot = (patient_id, thread_id, list(messages))


@pytest.mark.asyncio
async def test_save_history_also_updates_thread_snapshot():
    memory = RecordingMemory()
    orchestrator = ChatOrchestrator(memory=memory, graph_factory=lambda: None)

    await orchestrator._save_history(
        patient_id=1,
        thread_id="thread-1",
        history=[],
        user_message="我想挂号心内科",
        assistant_message="已为您找到今日可预约医生。",
    )

    assert memory.saved_messages is not None
    assert memory.saved_snapshot is not None
    assert memory.saved_snapshot[0] == 1
    assert memory.saved_snapshot[1] == "thread-1"
```

- [ ] **Step 2: 运行测试，确认当前只保存正文**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_orchestrator.py -q`

Expected: FAIL，`saved_snapshot is None`。

- [ ] **Step 3: 在 `_save_history()` 中追加线程摘要保存**

```python
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})
    await self._memory.save_messages(patient_id, thread_id, history)
    if hasattr(self._memory, "save_thread_snapshot"):
        await self._memory.save_thread_snapshot(patient_id, thread_id, history)
```

- [ ] **Step 4: 运行 orchestrator 测试**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_orchestrator.py -q`

Expected: PASS。

- [ ] **Step 5: 提交保存链路改造**

```bash
git add patient_agent_backend/app/chat/orchestrator.py patient_agent_backend/tests/test_api/test_chat_orchestrator.py
git commit -m "feat: persist chat thread snapshot metadata"
```

### Task 4: 前端在本地缓存失效时恢复线程列表并回填缓存

**Files:**
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/App.jsx`
- Modify: `patient_agent_frontend/src/storage/patientCache.js`
- Create: `patient_agent_frontend/src/storage/patientHistoryRecovery.test.js`

**Interfaces:**
- Consumes:
  - `chatApi.getThreads(): Promise<{ data: { threads: ThreadSummary[] } }>`
  - `chatApi.getHistory(threadId: string): Promise<{ data: { messages: list } }>`
  - `loadPatientThreads(patientId: number): ThreadSummary[]`
  - `savePatientThreads(patientId: number, threads: ThreadSummary[]): void`
  - `savePatientMessages(patientId: number, messagesMap: Record<string, Message[]>): void`
- Produces:
  - 页面初始化时，本地线程列表缺失则自动从 Redis 恢复
  - 恢复后的线程列表与正文重新写回浏览器缓存

- [ ] **Step 1: 写失败测试，锁定“本地空时恢复线程列表并回填缓存”**

```jsx
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { loadPatientThreads, savePatientThreads } from './patientCache.js'

describe('patient history recovery', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('writes recovered thread list back into patient scoped cache', () => {
    const recoveredThreads = [
      {
        id: 'thread-1',
        title: '我想挂号心内科',
        lastMessage: '已为您找到今日可预约医生。',
        time: '2026-06-27T14:00:00',
      },
    ]

    savePatientThreads(1, recoveredThreads)

    expect(loadPatientThreads(1)).toEqual(recoveredThreads)
  })
})
```

- [ ] **Step 2: 运行测试，确认需要前端恢复接线**

Run: `docker exec fm-patient-agent-frontend npm test -- src/storage/patientHistoryRecovery.test.js`

Expected: PASS 或最小缓存测试通过；随后继续通过页面改造锁定真实恢复流程。

- [ ] **Step 3: 在 `api/index.js` 中新增线程列表与删除请求**

```js
export const chatApi = {
  send(message, threadId) {
    return api.post('/chat', { message, thread_id: threadId })
  },
  sendStream(message, threadId) {
    const token = loadCurrentToken()
    return fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, thread_id: threadId }),
    })
  },
  getHistory(threadId) {
    return api.get('/chat/history', { params: { thread_id: threadId } })
  },
  getThreads() {
    return api.get('/chat/threads')
  },
  deleteThread(threadId) {
    return api.delete(`/chat/threads/${threadId}`)
  },
}
```

- [ ] **Step 4: 在 `App.jsx` 中实现线程列表恢复与回填**

```jsx
  useEffect(() => {
    let cancelled = false

    async function restoreThreads() {
      if (!patientId) {
        setThreads([])
        setMessagesMap({})
        setCurrentThreadId(null)
        return
      }

      const localThreads = loadPatientThreads(patientId)
      const localMessages = loadPatientMessages(patientId)
      setMessagesMap(localMessages)

      if (localThreads.length > 0) {
        setThreads(localThreads)
        setCurrentThreadId(null)
        return
      }

      try {
        const res = await chatApi.getThreads()
        if (cancelled) return
        const recoveredThreads = (res.data.threads || []).map((thread) => ({
          id: thread.thread_id,
          title: thread.title || '新对话',
          lastMessage: thread.last_message || '',
          time: thread.updated_at || new Date().toISOString(),
        }))
        setThreads(recoveredThreads)
        savePatientThreads(patientId, recoveredThreads)
        setCurrentThreadId(null)
      } catch {
        if (!cancelled) {
          setThreads([])
        }
      }
    }

    restoreThreads()
    return () => {
      cancelled = true
    }
  }, [patientId])
```

- [ ] **Step 5: 在切换线程时继续回填正文缓存**

```jsx
        const historyMsgs = (res.data.messages || []).map((m, i) => ({
          id: `${threadId}-hist-${i}`,
          role: m.role === 'assistant' ? 'ai' : m.role,
          text: m.content,
          time: new Date(),
        }))
        setMessagesMap((prev) => {
          const next = { ...prev, [threadId]: historyMsgs }
          savePatientMessages(patientId, next)
          return next
        })
```

- [ ] **Step 6: 删除线程时同步调用后端删除接口**

```jsx
  const deleteThread = useCallback(async (threadId) => {
    try {
      await chatApi.deleteThread(threadId)
    } catch {
      // ignore backend delete failure and still clear local cache
    }
    setThreads((prev) => prev.filter((t) => t.id !== threadId))
    setMessagesMap((prev) => {
      const next = { ...prev }
      delete next[threadId]
      return next
    })
    if (currentThreadId === threadId) {
      setCurrentThreadId(null)
    }
  }, [currentThreadId])
```

- [ ] **Step 7: 运行前端测试与构建**

Run: `docker exec fm-patient-agent-frontend sh -lc "npm test -- src/storage/patientCache.test.js src/storage/patientHistoryRecovery.test.js src/components/sidebar/sidebar-workbench.test.jsx && npm run build"`

Expected: PASS，前端测试与构建均成功。

- [ ] **Step 8: 提交前端恢复链路**

```bash
git add patient_agent_frontend/src/api/index.js patient_agent_frontend/src/App.jsx patient_agent_frontend/src/storage/patientCache.js patient_agent_frontend/src/storage/patientHistoryRecovery.test.js
git commit -m "feat: recover chat threads from redis"
```

## Self-Review

- **Spec coverage:** Task 1 覆盖 Redis 索引和摘要模型；Task 2 覆盖 `GET /api/chat/threads` 与删除接口；Task 3 覆盖正文保存时同步维护索引；Task 4 覆盖前端恢复线程列表、回填本地缓存、正文懒加载和删除一致性。
- **Placeholder scan:** 每个任务都给了具体文件、代码片段、命令和期望结果，没有 `TODO`、`TBD` 或“自行处理”类表述。
- **Type consistency:** 全计划统一使用 `patient_id`、`thread_id`、`save_thread_snapshot()`、`list_threads()`、`delete_thread()`、`chatApi.getThreads()`、`chatApi.deleteThread()` 这些接口名。
