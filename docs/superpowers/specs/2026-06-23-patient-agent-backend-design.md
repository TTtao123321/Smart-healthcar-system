# patient_agent_backend 技术方案

> **文档版本**：v1.0
> **编写日期**：2026-06-23
> **首期范围**：P0 — 基础服务（科室查询、医生排班、智能挂号）+ 安全护栏

---

## 1. 项目定位

patient_agent_backend 是智慧医疗助手的 Agent 后端，定位为**智能导诊员**（非 AI 医生）。通过 LangGraph 构建对话式 Agent，以工具调用方式获取医院信息系统（HMS）数据，为患者提供就医流程引导服务。

### 核心约束

- 不做疾病诊断、用药建议、报告解读
- 所有医疗决策转交真人医生
- 遵守《互联网诊疗管理办法》《生成式人工智能服务管理暂行办法》

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│            patient_agent_frontend (React)                │
│                  聊天界面 / 登录                           │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────────┐
│            patient_agent_backend (Python)                 │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                 FastAPI 网关层                        │ │
│  │  POST /api/chat   POST /api/auth   GET /api/sse     │ │
│  └────────────────────┬────────────────────────────────┘ │
│  ┌────────────────────▼────────────────────────────────┐ │
│  │             LangGraph Agent 引擎                     │ │
│  │                                                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │ │
│  │  │ 安全护栏  │  │ 对话管理  │  │  Tool Calling     │ │ │
│  │  │(输入/输出)│  │(状态图)   │  │  (选择→执行→返回) │ │ │
│  │  └──────────┘  └──────────┘  └───────────────────┘ │ │
│  └────────────────────┬────────────────────────────────┘ │
│  ┌────────────────────▼────────────────────────────────┐ │
│  │               工具层 (Tools)                         │ │
│  │  query_depts | query_doctors | query_schedules       │ │
│  │  create_registration | query_registration            │ │
│  └────────────────────┬────────────────────────────────┘ │
│  ┌────────────────────▼────────────────────────────────┐ │
│  │          hms_client (REST-RPC 风格客户端)             │ │
│  │   严格契约 | 服务化封装 | 统一异常 | 类型安全          │ │
│  └────────────────────┬────────────────────────────────┘ │
│  ┌────────────────────▼────────────────────────────────┐ │
│  │           Redis (对话记忆 / 缓存)                     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────┐
│         hospital_hms_api (Spring Boot)                    │
│            科室/医生/排班/挂号 等现有接口                    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. LangGraph Agent 状态图

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                    ┌────▼──────┐
                    │  输入护栏   │  敏感词拦截、高危识别、边界声明
                    │(guard_in) │
                    └────┬──────┘
                         │ safe
                    ┌────▼──────┐
                    │  LLM 推理  │  调用 LLM，决定直接回答或调用工具
                    │  (agent)  │
                    └────┬──────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         tool_call    直接回答    需转人工
              │          │          │
         ┌────▼─────┐   │    ┌────▼──────┐
         │  工具执行  │   │    │ 转人工提示  │
         │ (tools)  │   │    │(handoff)  │
         └────┬─────┘   │    └───────────┘
              │         │
         ┌────▼──────┐  │
         │  输出护栏   │  │  检查是否含医疗建议，附加免责声明
         │(guard_out)│  │
         └────┬──────┘  │
              │         │
              └────┬────┘
                   │
              ┌────▼─────┐
              │   END    │
              └──────────┘
```

### Agent 状态定义

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]          # 对话历史
    patient_id: str | None               # 当前患者 ID
    guardrail_result: str | None         # 护栏检查结果
    needs_handoff: bool                  # 是否需要转人工
    disclaimer_shown: bool               # 是否已展示免责声明
    conversation_turn: int               # 当前对话轮次
```

---

## 4. 核心模块设计

### 4.1 FastAPI 网关层 (`api/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 患者登录（复用 HMS 患者认证） |
| `/api/auth/register` | POST | 患者注册 |
| `/api/chat` | POST | 发送消息，返回完整响应 |
| `/api/chat/stream` | POST | 发送消息，SSE 流式返回 |
| `/api/chat/history` | GET | 获取对话历史 |

### 4.2 Agent 引擎 (`agent/`)

**graph.py** — LangGraph 图构建：

- 定义节点：`guard_in` → `agent` → `tools` → `guard_out`
- 条件边：`agent` 根据 LLM 输出路由到 `tools` / `END` / `handoff`
- 工具节点：使用 LangGraph 内置 `ToolNode`

**nodes.py** — 各节点实现：

| 节点 | 职责 |
|------|------|
| `guard_in` | 输入安全检查，返回 `guardrail_result` |
| `agent` | 调用 LLM，传入系统 Prompt + 工具定义 + 对话历史 |
| `tools` | 执行工具调用，将结果追加到消息列表 |
| `guard_out` | 输出安全检查，附加免责声明 |
| `handoff` | 生成转人工提示 |

### 4.3 工具层 (`tools/`)

首期 P0 工具清单：

| 工具名 | 功能 | 对接 HMS 接口 |
|--------|------|--------------|
| `query_departments` | 查询科室列表及介绍 | GET /medical_dept/list |
| `query_dept_detail` | 查询科室详情及诊室 | GET /medical_dept_sub/list |
| `query_doctors` | 按科室/姓名查询医生 | GET /doctor/list |
| `query_doctor_schedules` | 查询医生排班与号源 | GET /doctor_work_plan_schedule/list |
| `create_registration` | 创建挂号预约 | POST /medical_registration/save |
| `query_registration` | 查询挂号状态 | GET /medical_registration/info |
| `cancel_registration` | 取消挂号 | POST /medical_registration/cancel |

工具定义示例：

```python
from langchain_core.tools import tool

@tool
def query_departments(page: int = 1, page_size: int = 20) -> str:
    """查询医院所有科室列表，包含科室名称、楼层位置和简介。
    当患者询问"有哪些科室""XX科在几楼"时使用此工具。"""
    result = await hms_client.dept_service.list(
        DeptListRequest(page=page, page_size=page_size)
    )
    return result.model_dump_json()
```

### 4.4 安全护栏 (`guardrails/`)

#### 输入护栏 (`input_guard.py`)

| 检查类型 | 关键词示例 | 响应策略 |
|---------|-----------|---------|
| 医疗诊断拦截 | "诊断""治疗方案""吃什么药""严重吗" | "我无法提供医疗建议，请直接咨询医生" |
| 报告解读拦截 | "指标正常吗""报告有什么问题" | "我无法解读医疗报告，请携带报告咨询主治医生" |
| 高危应急 | "自杀""大出血""呼吸困难" | 推送急诊/心理危机热线，标记 `needs_handoff=True` |
| 边界声明 | 涉及健康/症状话题 | 附加免责声明 |

#### 输出护栏 (`output_guard.py`)

- 检查 LLM 响应是否包含医疗建议性内容
- 自动附加免责声明（首次对话 + 涉及健康话题时）
- 转人工触发：连续 3 轮无法理解 / 涉及投诉纠纷

#### 敏感词库 (`keywords.py`)

- 医疗诊断类关键词列表（正则匹配）
- 高危应急关键词列表（精确匹配）
- 可通过配置文件扩展，无需改代码

### 4.5 HMS Client — REST-RPC 风格 (`hms_client/`)

#### 设计原则

- **严格契约**：每个接口有明确的请求/响应 Pydantic 模型对
- **服务化封装**：按业务域组织为 Service 对象，工具层调用服务方法而非直接 HTTP
- **统一异常**：所有 HMS 错误转换为 `HmsClientError` 层次结构
- **类型安全**：全程 Pydantic 模型，IDE 自动补全 + 运行时校验

#### 模块结构

```
hms_client/
├── __init__.py
├── contract.py              # RPC 接口契约定义
├── client.py                # RPC 客户端（认证、重试、日志）
├── models.py                # 请求/响应 Pydantic 模型
├── exceptions.py            # 统一异常体系
└── services/
    ├── __init__.py
    ├── dept_service.py      # 科室服务
    ├── doctor_service.py    # 医生/排班服务
    └── registration_service.py  # 挂号服务
```

#### 契约定义 (`contract.py`)

```python
from typing import TypeAlias
from app.hms_client.models import (
    DeptListRequest, DeptListResponse,
    DeptDetailRequest, DeptDetailResponse,
    DoctorListRequest, DoctorListResponse,
    ScheduleListRequest, ScheduleListResponse,
    RegistrationCreateRequest, RegistrationCreateResponse,
    RegistrationQueryRequest, RegistrationQueryResponse,
    RegistrationCancelRequest, RegistrationCancelResponse,
)

class RequestResponsePair:
    request: type
    response: type

# 科室服务契约
DeptServiceContract = {
    "list":   RequestResponsePair(request=DeptListRequest,   response=DeptListResponse),
    "detail": RequestResponsePair(request=DeptDetailRequest,  response=DeptDetailResponse),
}

# 医生服务契约
DoctorServiceContract = {
    "list":      RequestResponsePair(request=DoctorListRequest,    response=DoctorListResponse),
    "schedules": RequestResponsePair(request=ScheduleListRequest,  response=ScheduleListResponse),
}

# 挂号服务契约
RegistrationServiceContract = {
    "create": RequestResponsePair(request=RegistrationCreateRequest, response=RegistrationCreateResponse),
    "query":  RequestResponsePair(request=RegistrationQueryRequest,  response=RegistrationQueryResponse),
    "cancel": RequestResponsePair(request=RegistrationCancelRequest, response=RegistrationCancelResponse),
}
```

#### 服务调用示例

```python
# 工具层调用 — 类型安全、契约约束
result = await hms_client.dept_service.list(
    DeptListRequest(page=1, page_size=10)
)
# result: DeptListResponse — IDE 可自动补全字段

result = await hms_client.registration_service.create(
    RegistrationCreateRequest(
        patient_id="P001",
        doctor_id="D001",
        schedule_id="S001",
    )
)
```

#### 异常体系 (`exceptions.py`)

```python
class HmsClientError(Exception):
    """HMS 客户端基础异常"""

class HmsTimeoutError(HmsClientError):
    """请求超时"""

class HmsNotFoundError(HmsClientError):
    """资源不存在（科室/医生/排班未找到）"""

class HmsServerError(HmsClientError):
    """HMS 服务端错误（5xx）"""

class HmsAuthError(HmsClientError):
    """认证失败"""
```

#### 客户端核心 (`client.py`)

```python
class HmsClient:
    """HMS REST-RPC 客户端"""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self.dept_service = DeptService(self._http)
        self.doctor_service = DoctorService(self._http)
        self.registration_service = RegistrationService(self._http)

    async def close(self):
        await self._http.aclose()
```

### 4.6 对话记忆 (`memory/`)

- 使用 LangGraph 内置的 `MemorySaver`（开发阶段）+ Redis 持久化（生产阶段）
- 按 `patient_id` + `thread_id` 隔离对话
- 对话历史保留最近 20 轮，更早的自动摘要压缩

---

## 5. 技术选型

| 组件 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.12+ | - |
| Web 框架 | FastAPI | 0.115+ | 异步、自动文档、类型安全 |
| Agent 框架 | LangGraph | 0.4+ | 状态图驱动、原生 Tool Calling |
| LLM | OpenAI GPT-4o-mini | - | 可通过配置切换 |
| HTTP 客户端 | httpx | 0.28+ | 异步、类型安全 |
| 对话记忆 | Redis + langgraph-checkpoint | - | 生产级持久化 |
| 数据校验 | Pydantic v2 | - | 请求/响应模型 |
| 配置管理 | pydantic-settings | - | 环境变量 + .env |
| ASGI | uvicorn | - | 高性能异步服务器 |
| 测试 | pytest + pytest-asyncio | - | 异步测试支持 |

---

## 6. 项目目录结构

```
patient_agent_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py                 # 聊天接口（普通 + SSE 流式）
│   │   └── auth.py                 # 患者认证接口
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py                # LangGraph 图定义与构建
│   │   ├── state.py                # Agent 状态模型
│   │   ├── nodes.py                # 图节点实现
│   │   └── prompts.py              # 系统 Prompt 模板
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── dept_tools.py           # 科室查询工具
│   │   ├── doctor_tools.py         # 医生/排班查询工具
│   │   └── registration_tools.py   # 挂号工具
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── input_guard.py          # 输入安全过滤
│   │   ├── output_guard.py         # 输出安全过滤
│   │   └── keywords.py             # 敏感词/高危词库
│   ├── hms_client/
│   │   ├── __init__.py
│   │   ├── contract.py             # RPC 接口契约定义
│   │   ├── client.py               # RPC 客户端入口
│   │   ├── models.py               # 请求/响应 Pydantic 模型
│   │   ├── exceptions.py           # 统一异常体系
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── dept_service.py
│   │       ├── doctor_service.py
│   │       └── registration_service.py
│   ├── memory/
│   │   ├── __init__.py
│   │   └── redis_memory.py         # Redis 对话记忆
│   └── config/
│       ├── __init__.py
│       └── settings.py             # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_agent/
│   ├── test_tools/
│   ├── test_guardrails/
│   └── test_hms_client/
├── pyproject.toml
├── Dockerfile
├── .env.example
└── 智慧医疗助手Agent_PRD.md          # 已有 PRD 文档
```

---

## 7. 系统 Prompt 设计

```python
SYSTEM_PROMPT = """你是XX医院智慧服务助手，仅提供就医流程引导和信息查询服务。

## 你的职责
- 帮助患者查询科室信息、医生排班、号源状态
- 引导患者完成挂号、查询挂号状态
- 提供就诊流程指引

## 严格禁止
- 不进行疾病诊断、不推测疾病名称
- 不提供治疗方案、用药建议
- 不解读检验检查报告
- 不评价医生水平

## 工作方式
1. 患者描述需求时，使用工具查询医院数据
2. 仅展示客观数据，不做主观判断
3. 涉及健康/症状话题时，必须附加免责声明
4. 无法回答的问题，建议患者咨询医生或转人工客服

## 免责声明
"以上信息仅供参考，不能替代医生面诊。如有身体不适，请尽快到院就诊。"
"""
```

---

## 8. 对接 HMS API 映射表

| Agent 工具 | HMS 接口 | HTTP 方法 | 说明 |
|-----------|---------|----------|------|
| query_departments | /medical_dept/list | GET | 科室列表 |
| query_dept_detail | /medical_dept_sub/list | GET | 诊室列表（按科室） |
| query_doctors | /doctor/list | GET | 医生列表（按科室/姓名） |
| query_doctor_schedules | /doctor_work_plan_schedule/list | GET | 排班与号源 |
| create_registration | /medical_registration/save | POST | 创建挂号 |
| query_registration | /medical_registration/info | GET | 查询挂号 |
| cancel_registration | /medical_registration/cancel | POST | 取消挂号 |

---

## 9. 部署方案

### Docker 集成

已在项目根目录 [docker-compose.yml](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/docker-compose.yml) 中新增 patient_agent_backend 服务(单 compose 一键启动方案,见 [.trae/documents/docker-one-click-startup-plan.md](file:///Users/bytedance/Desktop/mywork/.trae/documents/docker-one-click-startup-plan.md)):

```yaml
patient_agent_backend:
  build:
    context: ./patient_agent_backend
    dockerfile: Dockerfile
  ports:
    - "8001:8000"
  environment:
    - HMS_API_URL=http://hospital_hms_api:8080
    - REDIS_URL=redis://redis:6379/1
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - OPENAI_BASE_URL=${OPENAI_BASE_URL:-}
  depends_on:
    - redis
    - hospital_hms_api
```

### 前端代理

在 `patient_agent_frontend/vite.config.js` 中配置代理：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    }
  }
}
```

---

## 10. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| LLM 生成违规医疗建议 | 合规风险 | 输入/输出双层护栏 + 严格 Prompt + 关键词黑名单 |
| HMS API 变更导致工具失效 | 服务中断 | 契约层隔离，变更只影响 hms_client；集成测试覆盖 |
| OpenAI API 不可用 | 服务中断 | 配置 OPENAI_BASE_URL 支持代理/Azure 中转；降级为规则回复 |
| 高并发下 Redis 记忆膨胀 | 性能下降 | 对话历史限 20 轮 + 自动摘要压缩 |
| 患者误将 Agent 当医生 | 延误病情 | 强制边界声明、敏感词拦截、人工兜底 |

---

## 11. 后续迭代（P1-P3）

| 阶段 | 功能 | 新增工具 |
|------|------|---------|
| P1 | 候诊进度、院内导航、报告查询、缴费引导 | `query_queue_status`, `query_report`, `query_payment` |
| P2 | 症状分诊规则引擎、医生推荐、用药/复诊提醒 | `symptom_triage`, `recommend_doctor`, `set_medication_reminder` |
| P3 | 满意度评价、运营知识库管理后台 | `submit_feedback`, `search_faq` |
