# 智慧医疗助手 Agent 后端架构文档

## 一、整体架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                     patient_agent_frontend                       │
│                    (Vue 3, 端口 5174)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/SSE
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   patient_agent_backend                          │
│                   (FastAPI, 端口 8000)                           │
│                                                                  │
│  ┌──────────┐    ┌──────────────────────────────────────────┐   │
│  │  Auth    │    │              Chat API                     │   │
│  │ /api/auth│    │  /api/chat      /api/chat/stream         │   │
│  │          │    │  /api/chat/history                        │   │
│  └────┬─────┘    └──────────────────┬───────────────────────┘   │
│       │                             │                            │
│       │    ┌────────────────────────┼──────────────────────┐    │
│       │    │         LangGraph Agent Pipeline               │    │
│       │    │                                                │    │
│       │    │  guard_in ──► agent ──► should_continue        │    │
│       │    │                  │         │                    │    │
│       │    │                  │    ┌────┴────┐               │    │
│       │    │                  │    ▼         ▼               │    │
│       │    │                  │  guard_out  handoff         │    │
│       │    │                  │                              │    │
│       │    │  ┌───────────────┼─────────────────────────┐   │    │
│       │    │  │          Tools Layer                     │   │    │
│       │    │  │  query_departments   query_doctors       │   │    │
│       │    │  │  query_dept_detail   query_doctor_detail │   │    │
│       │    │  │  query_schedules     create_registration │   │    │
│       │    │  │  cancel_registration query_registration  │   │    │
│       │    │  └───────────────┬──────────────────────────┘   │    │
│       │    └──────────────────┼──────────────────────────────┘    │
│       │                       │                                   │
│       │    ┌──────────────────┼──────────────────────────────┐    │
│       │    │            HMS Client Layer                      │    │
│       │    │  HmsClient ─► DeptService / DoctorService       │    │
│       │    │              ─► RegistrationService              │    │
│       │    └──────────────────┬──────────────────────────────┘    │
│       │                       │                                   │
│       │    ┌──────────────────┼──────────────────────────────┐    │
│       │    │           Guardrails (安全护栏)                  │    │
│       │    │  input_guard.py  ─► 高危/诊断/报告/转人工        │    │
│       │    │  output_guard.py ─► 医疗建议检测 + 免责声明      │    │
│       │    └──────────────────┼──────────────────────────────┘    │
│       │                       │                                   │
│       │    ┌──────────────────┼──────────────────────────────┐    │
│       │    │           Memory (对话记忆)                       │    │
│       │    │  RedisMemory ─► Redis 持久化 7 天,最多 20 轮    │    │
│       │    └──────────────────┼──────────────────────────────┘    │
│       │                       │                                   │
│       └─── Redis ─────────────┘                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (SaToken 认证)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  hospital_hms_api (HMS 后端)                     │
│                  (Spring Boot, 端口 9091)                        │
│   /user/login  /dept/*  /doctor/*  /registration/*              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  MySQL        RabbitMQ
```

---

## 二、分层架构

### 1. 入口层 — `app/main.py`

FastAPI 应用入口,负责**启动时依赖注入**与**生命周期管理**:

```
启动流程 (lifespan):
  1. 创建 HmsClient → 登录 HMS 获取 SaToken
  2. init_tools(hms_client) → 把 9 个 LangChain Tool 注入 HMS 客户端
  3. compile_graph() → 预编译 LangGraph 状态图
  4. 创建 Redis 连接 → 初始化 RedisMemory (对话记忆)
  5. 注册 /api/chat + /api/auth 路由
  6. 注册 CORS 中间件
```

### 2. 路由层 — `app/api/`

| 路由 | 端点 | 功能 |
|---|---|---|
| `chat.py` | `POST /api/chat` | 普通对话 — 从 Redis 加载历史 → 构建 AgentState → 执行 graph → 保存历史 |
| | `POST /api/chat/stream` | SSE 流式对话 — 用 `graph.astream_events` 实时推送 LLM token |
| | `GET /api/chat/history` | 查询对话历史 |
| `auth.py` | `POST /api/auth/send-sms` | 发送验证码 (开发模式直接返回 code) |
| | `POST /api/auth/login` | 验证码登录,返回 UUID token + 缓存到 Redis |

**关键设计**: chat.py 不直接依赖 HMS 客户端,而是通过 `graph.ainvoke(state)` 把整个对话交给 LangGraph 管道处理,路由层只负责"进/出"两个环节。

---

### 3. Agent 引擎层 — `app/agent/`

基于 **LangGraph StateGraph** 实现的有状态 Agent 编排。

#### 3.1 状态定义 — `state.py`

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]        # 对话历史 (LangChain 消息)
    patient_id: str | None             # 当前患者 ID
    guardrail_result: str | None       # 护栏检查结果
    needs_handoff: bool                # 是否转人工
    disclaimer_shown: bool             # 免责声明是否已展示
    conversation_turn: int             # 当前对话轮次
```

#### 3.2 图结构 — `graph.py`

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│ guard_in │────▶│  agent   │────▶│should_continue│────▶│ guard_out│──▶ END
└──────────┘     └────┬─────┘     └──────┬───────┘     └──────────┘
                      │                  │
                      │ (LLM 调用工具)    │ (needs_handoff=True)
                      │                  ▼
                      │           ┌──────────┐
                      └──────────▶│ handoff  │──▶ END
                                  └──────────┘
```

**4 个节点 + 1 个条件路由**:

| 节点 | 职责 |
|---|---|
| `guard_in` | 输入安全护栏: 检查用户消息是否含高危/诊断/报告内容 |
| `agent` | LLM 推理 + 工具调用循环: 绑定 9 个 Tool,执行 tool_calls,再调 LLM 生成最终回复 |
| `should_continue` | 条件路由: 检查 `needs_handoff` 决定走 `guard_out` 还是 `handoff` |
| `guard_out` | 输出安全护栏: 检测 LLM 回复是否含医疗建议,附加免责声明 |
| `handoff` | 转人工: 返回固定转接消息 |

#### 3.3 agent 节点的工具调用循环

```
1. 构建 messages = [SystemMessage] + 对话历史
2. llm.ainvoke(messages) → 返回 AIMessage
3. 如果 AIMessage 包含 tool_calls:
   ├─ 遍历每个 tool_call,执行 tool.ainvoke(args)
   ├─ 把工具结果作为 HumanMessage 追加到 messages
   └─ 再次 llm.ainvoke(messages) → 生成最终自然语言回复
4. 返回 {"messages": [response]}
```

**关键设计**: 工具调用和 LLM 二次推理**都在 agent 这一个节点内完成**,不需要图层面的循环边,简化了图的复杂度。

#### 3.4 System Prompt — `prompts.py`

严格限定了 Agent 的行为边界:

- **只能做**: 科室查询、医生排班、号源查询、挂号引导
- **禁止做**: 疾病诊断、治疗方案、用药建议、报告解读、评价医生
- 涉及健康话题时,必须附加免责声明

---

### 4. 工具层 — `app/tools/`

9 个 LangChain Tool,采用**闭包工厂模式**注入 HMS 客户端:

| 工具 | 对应 HMS API |
|---|---|
| `query_departments` | `/dept/list` |
| `query_dept_detail` | `/dept/detail` |
| `query_doctors` | `/doctor/list` |
| `query_doctor_detail` | `/doctor/detail` |
| `query_doctor_schedules` | `/doctor/schedules` |
| `query_schedule_detail` | `/doctor/schedule/detail` |
| `create_registration` | `/registration/create` |
| `query_registration` | `/registration/query` |
| `cancel_registration` | `/registration/cancel` |

**闭包工厂模式**:

```python
# tools/__init__.py
def init_tools(hms_client: HmsClient) -> list:
    tools = (create_dept_tools(hms_client)      # 3 个
           + create_doctor_tools(hms_client)    # 4 个
           + create_registration_tools(hms_client))  # 2 个
    ALL_TOOLS.extend(tools)
```

每个 `create_*_tools` 函数用闭包捕获 `hms_client`,返回的 `@tool` 装饰的函数内部可以直接调用 HMS 服务,无需全局变量。这是最干净的依赖注入方式。

---

### 5. HMS 客户端层 — `app/hms_client/`

| 文件 | 职责 |
|---|---|
| `client.py` | 核心 HTTP 客户端: 管理 SaToken 认证、统一错误处理、封装 GET/POST |
| `models.py` | Pydantic 请求/响应模型 |
| `contract.py` | HMS API 契约定义 |
| `exceptions.py` | 自定义异常 (HmsAuthError / HmsTimeoutError / HmsServerError 等) |
| `services/dept_service.py` | 科室业务封装 |
| `services/doctor_service.py` (181 行) | 医生/排班业务封装 |
| `services/registration_service.py` (90 行) | 挂号业务封装 |

**认证流程**:

```
启动时: HmsClient.login_admin() → POST /user/login {username, password}
       → 获取 SaToken → 存入 self._http.headers["satoken"]
       → 后续所有请求自动携带 Token
```

**错误处理链**:

```
httpx.TimeoutException → HmsTimeoutError
httpx.RequestError     → HmsClientError
HTTP 401               → HmsAuthError
HTTP 404               → HmsNotFoundError
HTTP 4xx               → HmsValidationError
HTTP 5xx               → HmsServerError
HMS CommonResult.code≠200 → HmsClientError
```

---

### 6. 安全护栏层 — `app/guardrails/`

#### 输入护栏 — `input_guard.py`

5 级检查,优先级递减:

| 级别 | 触发条件 | 动作 |
|---|---|---|
| 1. 高危应急 | 关键词: 胸痛/呼吸困难/自杀/大出血... | 拦截 + 转人工 + 提示拨打 120 |
| 2. 医疗诊断 | 正则: "我得了什么病"/"是不是XX病" | 拦截 + 拒绝诊断 |
| 3. 报告解读 | 正则: "帮我看报告"/"化验单" | 拦截 + 拒绝解读 |
| 4. 转人工 | 正则: "人工"/"客服"/"投诉" | 标记 needs_handoff |
| 5. 边界声明 | 正则: "头疼"/"不舒服"/"症状" | 标记 needs_disclaimer |

#### 输出护栏 — `output_guard.py`

```
检查 LLM 回复中是否包含:
  - "建议你吃/服用XX药"    → 前插警告前缀
  - "你应该XX治疗"          → 前插警告前缀
  - "不需要就医"/"不严重"   → 前插警告前缀

如果是健康话题 + 首次展示 → 末尾追加免责声明
```

---

### 7. 记忆层 — `app/memory/redis_memory.py`

| 特性 | 实现 |
|---|---|
| 存储后端 | Redis (容器内 `redis:6379/1`) |
| Key 格式 | `chat:memory:{patient_id}:{thread_id}` |
| 过期时间 | 7 天 |
| 最大轮次 | 20 轮 (可配置) |
| 消息格式 | `[{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]` |

对话流程中,历史消息在 `/api/chat` 路由层加载/保存,Agent 图本身不感知存储。

---

### 8. 配置层 — `app/config/settings.py`

使用 `pydantic-settings`,自动从 `.env` 文件和**环境变量**加载:

| 配置项 | 默认值 | 容器环境变量 |
|---|---|---|
| `hms_api_url` | `http://localhost:8080` | `HMS_API_URL=http://hospital_hms_api:9091/hms` |
| `redis_url` | `redis://localhost:6379/1` | `REDIS_URL=redis://:123456@redis:6379/1` |
| `openai_api_key` | 空 | `OPENAI_API_KEY` |
| `openai_base_url` | None | `OPENAI_BASE_URL` |
| `openai_model` | `gpt-4o-mini` | `OPENAI_MODEL` |

---

## 三、一次完整对话的数据流

```
用户输入: "我头疼应该挂哪个科"
    │
    ▼
POST /api/chat {message: "我头疼...", patient_id: "xxx"}
    │
    ├─ 1. RedisMemory.load_messages() → 加载历史
    ├─ 2. 构建 AgentState
    │
    ▼
graph.ainvoke(state)
    │
    ├─ 3. guard_in → check_input("我头疼...")
    │     ├─ 不匹配高危/诊断/报告
    │     └─ 匹配 health_topic → needs_disclaimer=True
    │
    ├─ 4. agent → LLM.ainvoke([SystemMessage, HumanMessage("我头疼...")])
    │     ├─ LLM 决定调用 query_departments()
    │     ├─ 工具执行 → 返回科室列表 JSON
    │     ├─ LLM 再次推理 → 生成回复: "根据您的症状,建议挂神经内科..."
    │     │
    │     └─ 返回 AIMessage("建议挂神经内科...")
    │
    ├─ 5. should_continue → needs_handoff=False → "end"
    │
    ├─ 6. guard_out → check_output("建议挂神经内科...")
    │     ├─ 不匹配医疗建议模式
    │     └─ needs_disclaimer=True + disclaimer_shown=False → 追加免责声明
    │
    └─ 7. 返回最终 State
    │
    ▼
路由层提取最后一条 AIMessage.content
    │
    ├─ 8. RedisMemory.save_messages() → 持久化对话
    │
    └─ 9. 返回 JSON: {"message": "建议挂神经内科...\n\n⚠️ 以上信息仅供参考..."}
```

---

## 四、技术栈

| 层级 | 技术 |
|---|---|
| Web 框架 | FastAPI + Uvicorn |
| Agent 框架 | LangGraph (StateGraph) |
| LLM | LangChain ChatOpenAI (兼容 OpenAI API 的任何模型) |
| 工具定义 | LangChain `@tool` 装饰器 |
| 数据验证 | Pydantic v2 |
| HTTP 客户端 | httpx (异步) |
| 对话记忆 | Redis (aioredis) |
| 流式输出 | SSE (sse-starlette) |
| 配置管理 | pydantic-settings |
| 依赖管理 | pyproject.toml (PEP 621) |
| 容器化 | Docker (python:3.12-slim) |

---

## 五、架构设计亮点

| 亮点 | 实现 |
|---|---|
| **关注点分离** | 路由/Agent/工具/护栏/记忆 5 层独立,每层只做一件事 |
| **依赖注入** | 工具用闭包注入 HMS 客户端,记忆/认证用 `set_*` 注入,无全局变量 |
| **安全优先** | 输入/输出双护栏,5 级输入检查 + 医疗建议检测 + 免责声明 |
| **LLM 缓存** | `_get_llm()` 复用 ChatOpenAI 实例,避免每次请求重建 |
| **图缓存** | `compile_graph()` 只编译一次,后续请求直接复用 |
| **流式支持** | SSE 通过 `graph.astream_events` 实时推送 token |
| **错误隔离** | HMS 客户端分层异常,工具执行失败不中断整个图 |
| **多轮对话** | Redis 持久化,支持跨请求的 thread_id 级别对话上下文 |
| **跨机部署** | Docker Compose 一键启动,镜像源可参数化 |

---

## 六、当前局限与演进方向

| 局限 | 影响 | 改进方向 |
|---|---|---|
| agent 节点只做一轮工具调用 | 复杂场景 (先查科室再查医生再挂号) 需要多轮对话 | 加 ReAct 循环,或引入子图 |
| 患者 ID 未关联 HMS | 挂号时 `patient_card_id` 需前端传入 | 登录后从 HMS 获取真实患者 ID |
| 工具结果是原始 JSON | LLM 需要解析 JSON 字符串 | 增加结构化输出中间层 |
| 无流控/限流 | 恶意请求可打满 LLM 配额 | 加 Redis 令牌桶 |
| 无用户认证中间件 | 所有 API 未验证 token | 添加 FastAPI 依赖注入鉴权 |

---

## 七、目录结构

```
patient_agent_backend/
├── Dockerfile                    # 多阶段构建 (Python 3.12-slim)
├── pyproject.toml                # 依赖声明 (FastAPI/LangGraph/LangChain/Redis)
├── app/
│   ├── main.py                   # FastAPI 应用入口 + 生命周期管理
│   ├── api/
│   │   ├── auth.py               # 认证接口 (短信验证码登录)
│   │   └── chat.py               # 聊天接口 (普通 + SSE 流式)
│   ├── agent/
│   │   ├── graph.py              # LangGraph 图定义与编译
│   │   ├── nodes.py              # 图节点实现 (guard_in/agent/guard_out/handoff)
│   │   ├── state.py              # AgentState 状态定义
│   │   └── prompts.py            # System Prompt + 转人工消息模板
│   ├── tools/
│   │   ├── __init__.py           # 工具统一导出 + 闭包工厂注入
│   │   ├── dept_tools.py         # 科室查询工具 (2 个)
│   │   ├── doctor_tools.py       # 医生/排班查询工具 (4 个)
│   │   └── registration_tools.py # 挂号工具 (3 个)
│   ├── hms_client/
│   │   ├── client.py             # HMS HTTP 客户端核心
│   │   ├── models.py             # 请求/响应 Pydantic 模型
│   │   ├── contract.py           # API 契约定义
│   │   ├── exceptions.py         # 自定义异常
│   │   └── services/
│   │       ├── dept_service.py   # 科室业务服务
│   │       ├── doctor_service.py # 医生/排班业务服务
│   │       └── registration_service.py # 挂号业务服务
│   ├── guardrails/
│   │   ├── input_guard.py        # 输入安全护栏
│   │   ├── output_guard.py       # 输出安全护栏
│   │   └── keywords.py           # 敏感词库
│   ├── memory/
│   │   └── redis_memory.py       # Redis 对话记忆管理
│   └── config/
│       └── settings.py           # 配置管理 (pydantic-settings)
└── tests/                        # 测试目录
```