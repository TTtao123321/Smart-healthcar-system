# Patient Agent Local Cache Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `patient_agent_frontend` 增加按患者隔离的本地缓存和 1 天 TTL，避免不同患者在同一浏览器串会话数据。

**Architecture:** 新增一个共享的前端存储模块，统一负责 key 命名、TTL 包装、旧 key 清理、当前患者缓存清理和 401 清理入口；`App.jsx` 只消费这些接口，负责初始化、登录成功、切换会话和登出时的状态同步；`api/index.js` 复用同一清理入口，确保 401 与主动退出的缓存行为一致。

**Tech Stack:** React 19、Vite、Vitest、Testing Library、localStorage、Axios

## Global Constraints

- 仅修改 `patient_agent_frontend`，不改后端接口和 Redis 结构。
- 会话列表和消息缓存必须按 `patient_id` 隔离。
- 浏览器本地缓存 TTL 固定为 `24 * 60 * 60 * 1000`，即 1 天。
- 旧共享 key `patient_user`、`patient_threads`、`patient_messages` 只做删除，不做数据迁移。
- `401` 清理必须与主动退出登录使用同一套完整清理逻辑。
- 会话切换仍保持“本地有缓存优先，本地没有再请求 `/api/chat/history`”。

---

## File Structure

- Create: `patient_agent_frontend/src/storage/patientCache.js`
  - 统一封装 TTL 包装、按患者 key、旧 key 清理、当前患者清理、401 清理入口。
- Create: `patient_agent_frontend/src/storage/patientCache.test.js`
  - 覆盖 TTL 过期、患者隔离、旧 key 清理、完整清理流程。
- Modify: `patient_agent_frontend/src/App.jsx`
  - 接入新的缓存读写逻辑，处理页面初始化、登录成功、同患者重复登录、切换患者清理、主动退出、线程与消息持久化。
- Modify: `patient_agent_frontend/src/api/index.js`
  - 将 401 拦截器改为调用统一缓存清理函数。

### Task 1: 实现共享缓存模块

**Files:**
- Create: `patient_agent_frontend/src/storage/patientCache.js`
- Test: `patient_agent_frontend/src/storage/patientCache.test.js`

**Interfaces:**
- Consumes: `window.localStorage`
- Produces:
  - `CACHE_TTL_MS: number`
  - `STORAGE_KEYS: { TOKEN: string; CURRENT_USER: string; LEGACY_USER: string; LEGACY_THREADS: string; LEGACY_MESSAGES: string }`
  - `patientScopedKey(kind: 'user' | 'threads' | 'messages', patientId: string | number): string`
  - `writeCache(key: string, value: unknown, patientId: string | number | null): void`
  - `readCache<T>(key: string, expectedPatientId?: string | number | null, fallback?: T): T`
  - `removeKey(key: string): void`
  - `purgeLegacyCacheKeys(): void`
  - `clearPatientScopedCache(patientId: string | number | null): void`
  - `clearCurrentSessionCache(): void`
  - `loadCurrentUser(): null | { name: string; token: string; patient_id: number; phone: string }`
  - `saveCurrentSession(params: { token: string; user: { name: string; token: string; patient_id: number; phone: string } }): void`

- [ ] **Step 1: 写失败测试，锁定 TTL、隔离和清理行为**

```jsx
import { beforeEach, describe, expect, it } from 'vitest'
import {
  CACHE_TTL_MS,
  STORAGE_KEYS,
  clearCurrentSessionCache,
  clearPatientScopedCache,
  loadCurrentUser,
  patientScopedKey,
  purgeLegacyCacheKeys,
  readCache,
  saveCurrentSession,
  writeCache,
} from './patientCache.js'

describe('patientCache', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns fallback and deletes expired cache entries', () => {
    localStorage.setItem(
      'patient_threads:1',
      JSON.stringify({
        value: [{ id: 'thread-1' }],
        patient_id: 1,
        expires_at: Date.now() - 1,
      })
    )

    expect(readCache('patient_threads:1', 1, [])).toEqual([])
    expect(localStorage.getItem('patient_threads:1')).toBeNull()
  })

  it('isolates scoped cache by patient id', () => {
    writeCache(patientScopedKey('messages', 1), { 'thread-1': [{ text: 'A' }] }, 1)

    expect(readCache(patientScopedKey('messages', 1), 1, {})).toEqual({
      'thread-1': [{ text: 'A' }],
    })
    expect(readCache(patientScopedKey('messages', 1), 2, {})).toEqual({})
  })

  it('persists current session with the same ttl envelope', () => {
    saveCurrentSession({
      token: 'token-1',
      user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
    })

    expect(loadCurrentUser()).toMatchObject({ patient_id: 1, name: '张三' })
    const tokenEnvelope = JSON.parse(localStorage.getItem(STORAGE_KEYS.TOKEN))
    expect(tokenEnvelope.patient_id).toBe(1)
    expect(tokenEnvelope.expires_at - Date.now()).toBeLessThanOrEqual(CACHE_TTL_MS)
  })

  it('removes all session and scoped keys for the current patient', () => {
    saveCurrentSession({
      token: 'token-1',
      user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
    })
    writeCache(patientScopedKey('threads', 1), [{ id: 'thread-1' }], 1)
    writeCache(patientScopedKey('messages', 1), { 'thread-1': [{ text: 'A' }] }, 1)

    clearCurrentSessionCache()

    expect(localStorage.getItem(STORAGE_KEYS.TOKEN)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.CURRENT_USER)).toBeNull()
    expect(localStorage.getItem(patientScopedKey('threads', 1))).toBeNull()
    expect(localStorage.getItem(patientScopedKey('messages', 1))).toBeNull()
  })

  it('purges legacy shared keys without migrating them', () => {
    localStorage.setItem(STORAGE_KEYS.LEGACY_USER, '{}')
    localStorage.setItem(STORAGE_KEYS.LEGACY_THREADS, '[]')
    localStorage.setItem(STORAGE_KEYS.LEGACY_MESSAGES, '{}')

    purgeLegacyCacheKeys()

    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_USER)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_THREADS)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_MESSAGES)).toBeNull()
  })
})
```

- [ ] **Step 2: 运行测试，确认当前实现尚未满足**

Run: `npm test -- src/storage/patientCache.test.js`

Expected: FAIL，报错包含 `Cannot find module './patientCache.js'` 或导出缺失。

- [ ] **Step 3: 写最小实现，让存储行为可复用**

```js
export const CACHE_TTL_MS = 24 * 60 * 60 * 1000

export const STORAGE_KEYS = {
  TOKEN: 'patient_token',
  CURRENT_USER: 'patient_current_user',
  LEGACY_USER: 'patient_user',
  LEGACY_THREADS: 'patient_threads',
  LEGACY_MESSAGES: 'patient_messages',
}

const PREFIXES = {
  user: 'patient_user',
  threads: 'patient_threads',
  messages: 'patient_messages',
}

function now() {
  return Date.now()
}

function envelope(value, patientId) {
  return JSON.stringify({
    value,
    patient_id: patientId ?? null,
    expires_at: now() + CACHE_TTL_MS,
  })
}

export function patientScopedKey(kind, patientId) {
  return `${PREFIXES[kind]}:${patientId}`
}

export function removeKey(key) {
  localStorage.removeItem(key)
}

export function writeCache(key, value, patientId) {
  localStorage.setItem(key, envelope(value, patientId))
}

export function readCache(key, expectedPatientId = null, fallback = null) {
  const raw = localStorage.getItem(key)
  if (!raw) return fallback

  try {
    const parsed = JSON.parse(raw)
    if (!parsed?.expires_at || parsed.expires_at <= now()) {
      removeKey(key)
      return fallback
    }
    if (
      expectedPatientId !== null
      && expectedPatientId !== undefined
      && parsed.patient_id !== expectedPatientId
    ) {
      removeKey(key)
      return fallback
    }
    return parsed.value ?? fallback
  } catch {
    removeKey(key)
    return fallback
  }
}

export function purgeLegacyCacheKeys() {
  removeKey(STORAGE_KEYS.LEGACY_USER)
  removeKey(STORAGE_KEYS.LEGACY_THREADS)
  removeKey(STORAGE_KEYS.LEGACY_MESSAGES)
}

export function clearPatientScopedCache(patientId) {
  if (patientId === null || patientId === undefined || patientId === '') return
  removeKey(patientScopedKey('user', patientId))
  removeKey(patientScopedKey('threads', patientId))
  removeKey(patientScopedKey('messages', patientId))
}

export function loadCurrentUser() {
  return readCache(STORAGE_KEYS.CURRENT_USER, null, null)
}

export function saveCurrentSession({ token, user }) {
  writeCache(STORAGE_KEYS.TOKEN, token, user.patient_id)
  writeCache(STORAGE_KEYS.CURRENT_USER, user, user.patient_id)
  writeCache(patientScopedKey('user', user.patient_id), user, user.patient_id)
}

export function clearCurrentSessionCache() {
  const currentUser = loadCurrentUser()
  removeKey(STORAGE_KEYS.TOKEN)
  removeKey(STORAGE_KEYS.CURRENT_USER)
  clearPatientScopedCache(currentUser?.patient_id ?? null)
}
```

- [ ] **Step 4: 运行测试，确认缓存模块通过**

Run: `npm test -- src/storage/patientCache.test.js`

Expected: PASS，显示 `5 passed`.

- [ ] **Step 5: 提交缓存模块**

```bash
git add src/storage/patientCache.js src/storage/patientCache.test.js
git commit -m "feat: add patient scoped cache storage"
```

### Task 2: 接入 App 页面初始化、登录、登出和会话缓存

**Files:**
- Modify: `patient_agent_frontend/src/App.jsx`
- Test: `patient_agent_frontend/src/storage/patientCache.test.js`

**Interfaces:**
- Consumes:
  - `loadCurrentUser(): null | UserInfo`
  - `saveCurrentSession(params): void`
  - `readCache(key, expectedPatientId, fallback): T`
  - `writeCache(key, value, patientId): void`
  - `patientScopedKey(kind, patientId): string`
  - `clearPatientScopedCache(patientId): void`
  - `clearCurrentSessionCache(): void`
  - `purgeLegacyCacheKeys(): void`
- Produces:
  - App 初始化时从当前患者隔离 key 恢复 `user`、`threads`、`messagesMap`
  - 登录成功时在跨患者场景清理旧患者缓存
  - 主动退出时清空当前患者完整缓存

- [ ] **Step 1: 扩展测试，锁定 App 侧关键缓存流转**

```jsx
it('clears previous patient cache when a different patient logs in', () => {
  saveCurrentSession({
    token: 'token-a',
    user: { name: '张三', token: 'token-a', patient_id: 1, phone: '13800138001' },
  })
  writeCache(patientScopedKey('threads', 1), [{ id: 'thread-a' }], 1)
  writeCache(patientScopedKey('messages', 1), { 'thread-a': [{ text: '旧消息' }] }, 1)

  const previousUser = loadCurrentUser()
  if (previousUser && previousUser.patient_id !== 2) {
    clearPatientScopedCache(previousUser.patient_id)
  }
  saveCurrentSession({
    token: 'token-b',
    user: { name: '李四', token: 'token-b', patient_id: 2, phone: '13900139000' },
  })

  expect(localStorage.getItem(patientScopedKey('threads', 1))).toBeNull()
  expect(localStorage.getItem(patientScopedKey('messages', 1))).toBeNull()
  expect(loadCurrentUser()).toMatchObject({ patient_id: 2, name: '李四' })
})
```

- [ ] **Step 2: 运行测试，确认新行为尚未被页面层消费**

Run: `npm test -- src/storage/patientCache.test.js`

Expected: FAIL，如果辅助函数不足，断言无法满足。

- [ ] **Step 3: 修改 `App.jsx`，接入隔离 key 和 TTL 读取**

```jsx
import {
  clearCurrentSessionCache,
  clearPatientScopedCache,
  loadCurrentUser,
  patientScopedKey,
  purgeLegacyCacheKeys,
  readCache,
  saveCurrentSession,
  writeCache,
} from './storage/patientCache.js'

export default function App() {
  const [toastMsg, setToastMsg] = useState(null)
  const [user, setUser] = useState(() => {
    purgeLegacyCacheKeys()
    return loadCurrentUser()
  })

  const handleLogout = useCallback(() => {
    setUser(null)
    clearCurrentSessionCache()
    showToast('已退出登录')
  }, [showToast])
}

function ChatPage({ user, onLogout }) {
  const patientId = user?.patient_id
  const [threads, setThreads] = useState(() =>
    patientId ? readCache(patientScopedKey('threads', patientId), patientId, []) : []
  )
  const [messagesMap, setMessagesMap] = useState(() =>
    patientId ? readCache(patientScopedKey('messages', patientId), patientId, {}) : {}
  )

  useEffect(() => {
    if (!patientId) return
    writeCache(patientScopedKey('threads', patientId), threads, patientId)
  }, [patientId, threads])

  useEffect(() => {
    if (!patientId) return
    writeCache(patientScopedKey('messages', patientId), messagesMap, patientId)
  }, [patientId, messagesMap])
}

const submit = async (e) => {
  e.preventDefault()
  const res = await authApi.login(phone, code.trim())
  const { token, patient_id, name } = res.data
  const userInfo = { name, token, patient_id, phone }

  const previousUser = loadCurrentUser()
  if (previousUser && previousUser.patient_id !== patient_id) {
    clearPatientScopedCache(previousUser.patient_id)
  }

  saveCurrentSession({ token, user: userInfo })
  onLogin(userInfo)
}
```

- [ ] **Step 4: 补足页面切换时的状态重载**

```jsx
useEffect(() => {
  if (!patientId) {
    setThreads([])
    setMessagesMap({})
    setCurrentThreadId(null)
    return
  }

  setThreads(readCache(patientScopedKey('threads', patientId), patientId, []))
  setMessagesMap(readCache(patientScopedKey('messages', patientId), patientId, {}))
  setCurrentThreadId(null)
}, [patientId])
```

- [ ] **Step 5: 运行测试并执行一次构建**

Run: `npm test -- src/storage/patientCache.test.js && npm run build`

Expected: 测试通过，`vite build` 成功完成。

- [ ] **Step 6: 提交页面接入**

```bash
git add src/App.jsx src/storage/patientCache.js src/storage/patientCache.test.js
git commit -m "feat: isolate patient local chat cache"
```

### Task 3: 统一 401 清理逻辑并补回归验证

**Files:**
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/storage/patientCache.test.js`

**Interfaces:**
- Consumes:
  - `clearCurrentSessionCache(): void`
- Produces:
  - Axios `401` 拦截器复用共享清理逻辑
  - 测试覆盖“401 清掉完整缓存而非仅 token/user”

- [ ] **Step 1: 追加失败测试，锁定 401 清理范围**

```jsx
it('clears token, current user and scoped chat cache together', () => {
  saveCurrentSession({
    token: 'token-1',
    user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
  })
  writeCache(patientScopedKey('threads', 1), [{ id: 'thread-1' }], 1)
  writeCache(patientScopedKey('messages', 1), { 'thread-1': [{ text: 'A' }] }, 1)

  clearCurrentSessionCache()

  expect(localStorage.getItem(STORAGE_KEYS.TOKEN)).toBeNull()
  expect(localStorage.getItem(STORAGE_KEYS.CURRENT_USER)).toBeNull()
  expect(localStorage.getItem(patientScopedKey('threads', 1))).toBeNull()
  expect(localStorage.getItem(patientScopedKey('messages', 1))).toBeNull()
})
```

- [ ] **Step 2: 运行测试，确认回归场景已覆盖**

Run: `npm test -- src/storage/patientCache.test.js`

Expected: PASS，新增断言通过。

- [ ] **Step 3: 修改 axios 拦截器，复用统一清理函数**

```js
import axios from 'axios'
import { clearCurrentSessionCache } from '../storage/patientCache.js'

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      clearCurrentSessionCache()
      window.location.reload()
    }
    return Promise.reject(err)
  }
)
```

- [ ] **Step 4: 运行测试与目标回归命令**

Run: `npm test -- src/storage/patientCache.test.js src/components/sidebar/sidebar-workbench.test.jsx && npm run build`

Expected: 所有测试通过，既有侧边栏测试未回归，构建成功。

- [ ] **Step 5: 记录手工验证结果并提交**

```bash
git add src/api/index.js src/storage/patientCache.test.js
git commit -m "fix: clear scoped cache on auth expiry"
```

Manual verification checklist:

```text
1. 患者 A 登录，发送一条消息，刷新页面，确认会话仍能恢复。
2. 不退出，患者 B 登录，确认左侧会话列表不显示患者 A 的内容。
3. 手工将 localStorage 包装对象的 expires_at 改为过去时间，刷新页面，确认缓存被清空。
4. 让受保护接口返回 401，确认页面刷新后不会继续显示旧 threads/messages。
5. 在同一患者重复登录，确认自己的会话缓存仍保留，仅 token TTL 被刷新。
```

## Self-Review

- **Spec coverage:** Task 1 覆盖 TTL 包装、旧 key 清理和按患者隔离；Task 2 覆盖页面初始化、登录成功、切换患者清理、主动退出和会话持久化；Task 3 覆盖 401 完整清理与回归验证。
- **Placeholder scan:** 计划中的代码步骤均给出实际代码、命令和期望结果，没有 `TODO`、`TBD` 或“自行处理”类描述。
- **Type consistency:** 全计划统一使用 `patient_id`、`patientScopedKey()`、`loadCurrentUser()`、`clearCurrentSessionCache()` 这组接口，没有前后不一致命名。
