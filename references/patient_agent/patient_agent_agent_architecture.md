# patient_agent Agent 架构说明

> **文档目标**：面向后续开发、重构和跨角色对齐，说明 `patient_agent` 当前真实的 Agent 架构、执行链路、状态分层和修改入口。
> **适用范围**：`patient_agent_backend`、`patient_agent_frontend` 以及 `references/patient_agent` 下的架构对齐工作。
> **更新时间**：2026-06-29

---

## 1. 文档定位

这份文档聚焦的是 **Agent 架构本身**，不是泛化的后端系统说明。

重点回答 4 个问题：

1. `patient_agent` 现在到底是不是多 Agent 架构？
2. 一条消息从前端进入后，实际经过了哪些模块？
3. 为什么当前代码同时存在 `AgentState` 和 `FlowState` 两套状态？
4. 如果后续要新增能力或重构，应该优先改哪一层？

结论先行：

- 当前实现 **不是多 Agent / Supervisor / Router-Agent 架构**。
- 当前实现是 **单 LangGraph Agent + 规则预路由 + 工具集合 + Redis 双状态存储**。
- 真正决定系统行为的核心不只是在 `graph.py`，而是在：
  - `app/chat/orchestrator.py`
  - `app/chat/pre_router.py`
  - `app/agent/tool_runtime.py`
  - `app/chat/flow_state.py`

---

## 2. 一句话架构结论

`patient_agent` 当前采用的是一套面向挂号与医疗服务咨询场景的 **单 Agent 编排架构**：

- 用 `FastAPI` 提供聊天、患者信息和侧栏动作接口
- 用 `ChatOrchestrator` 统一收口聊天编排
- 用 `pre_router` 处理高确定性的业务动作
- 用 `LangGraph` 承载单 Agent 的安全护栏、LLM 推理和转人工分支
- 用工具层连接 HMS 能力
- 用 `RedisMemory` 保存对话历史
- 用 `FlowState` 保存线程级业务流程状态
- 用前端 SSE 将思考、工具调用和最终回复实时展示给用户

---

## 3. 总体架构图

```text
┌──────────────────────────────────────────────────────────────┐
│                    patient_agent_frontend                    │
│  ChatPage / Sidebar / Profile                               │
│  - 发起 /api/chat/stream                                    │
│  - 发起 /api/patient/sidebar/action                         │
│  - 展示 thinking / tool_start / tool_end / message          │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTP / SSE
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    patient_agent_backend                     │
│                                                              │
│  API Layer                                                   │
│  - /api/chat                                                 │
│  - /api/chat/stream                                          │
│  - /api/patient/sidebar/action                               │
│                                                              │
│  ChatOrchestrator                                            │
│  - 加载历史                                                   │
│  - 设置 request context                                      │
│  - try_pre_route                                             │
│  - 执行 graph                                                │
│  - 保存历史                                                   │
│                                                              │
│  Deterministic Pre Router                                    │
│  - query_registration                                        │
│  - create_registration(confirm)                              │
│  - cancel flow prompt                                        │
│                                                              │
│  LangGraph Single Agent                                      │
│  guard_in -> agent -> (handoff | guard_out) -> END           │
│                                                              │
│  Tool Runtime                                                │
│  - 执行 tool_calls                                           │
│  - 回灌工具结果给 LLM                                         │
│  - 控制最大轮次                                               │
│                                                              │
│  State Layer                                                 │
│  - AgentState: 图内编排状态                                  │
│  - FlowState: 线程级业务流程状态                             │
│                                                              │
│  Memory / External                                           │
│  - RedisMemory                                               │
│  - RedisFlowStateStore                                       │
│  - HMS Client / Services                                     │
└─────────────────────────────┬────────────────────────────────┘
                              ▼
                    hospital_hms_api / MySQL
```

---

## 4. 核心模块职责

### 4.1 入口与装配层

后端应用入口是 `patient_agent_backend/app/main.py`。

启动时完成以下装配：

1. 初始化 `HmsClient`
2. 调用 `init_tools(hms_client)` 注入工具
3. 编译 LangGraph
4. 初始化 `RedisMemory`
5. 初始化 `RedisFlowStateStore`
6. 注册认证、聊天、患者信息、侧栏和 E2E 路由

这一层的职责不是业务判断，而是 **依赖注入和生命周期管理**。

### 4.2 ChatOrchestrator 编排层

核心文件：`patient_agent_backend/app/chat/orchestrator.py`

这是当前架构的真实中枢，主要职责：

- 从记忆层加载线程历史
- 构造 `AgentState`
- 把 `session` 和 `thread_id` 写入上下文变量
- 优先尝试 `pre_router`
- 未命中时执行 graph
- 从 graph 结果中抽取最终可见回复
- 保存新的历史消息
- 在 SSE 模式下拆分 `thinking`、`tool_start`、`tool_end`、`message`、`done`

可以把它理解为：

```text
API 层负责收请求
ChatOrchestrator 负责组织一次完整对话执行
LangGraph 只负责其中的模型推理和护栏分支
```

### 4.3 LangGraph Agent 图层

核心文件：

- `patient_agent_backend/app/agent/graph.py`
- `patient_agent_backend/app/agent/nodes.py`

图结构非常简单：

```text
guard_in -> agent -> should_continue
                         ├─ end     -> guard_out -> END
                         └─ handoff -> handoff   -> END
```

图里只有 4 个节点：

- `guard_in`
  - 输入安全护栏
  - 判断是否属于诊断、报告解读、紧急高危、转人工等场景
- `agent`
  - 调 LLM
  - 如果 LLM 触发工具调用，则在节点内部完成工具循环
- `guard_out`
  - 处理输出修正
  - 在健康相关话题补免责声明
- `handoff`
  - 返回转人工固定话术

这个图的特点是 **图很轻，逻辑很重**：

- 图本身只有少量节点
- 真正复杂的部分在节点内部，尤其是 `agent` 节点和 `tool_runtime`

### 4.4 规则预路由层

核心文件：`patient_agent_backend/app/chat/pre_router.py`

这一层是当前实现里非常关键、也最容易被忽略的部分。

它的定位不是“意图分类器”，而是 **高确定性请求的旁路执行器**。

当前主要处理三类请求：

- 查询我的挂号
- 取消挂号前的记录选择引导
- 基于待确认上下文的挂号确认

也就是说，系统并不是所有事情都交给 LLM 决定，而是：

- 能用规则稳定命中的动作，直接调工具
- 需要自然语言理解或多步推理时，再交给 Agent

这是当前系统稳定性的关键来源之一。

### 4.5 工具运行时

核心文件：`patient_agent_backend/app/agent/tool_runtime.py`

职责：

- 标准化模型产生的 `tool_calls`
- 在工具名为空时尝试按关键词回退修复
- 顺序执行工具
- 把工具结果包装成消息回灌给 LLM
- 限制最大工具轮次
- 对工具返回进行错误类型归类

这意味着当前工具调用不是 LangGraph 图层面的多轮边循环，而是 **在单个 `agent` 节点内完成闭环**。

### 4.6 状态层

当前有两套状态：

#### A. `AgentState`

文件：`patient_agent_backend/app/agent/state.py`

用于图内编排，只保存最小必需状态：

- `messages`
- `patient_id`
- `guardrail_result`
- `needs_handoff`
- `disclaimer_shown`
- `conversation_turn`

#### B. `FlowState`

文件：`patient_agent_backend/app/chat/flow_state.py`

用于保存线程级业务流程状态，例如：

- 当前已选择科室
- 当前已选择医生
- 当前已选择排班
- 候选时段列表
- 待确认挂号信息

这是当前架构最关键的设计点之一：

- `AgentState` 解决“模型如何运行”
- `FlowState` 解决“挂号流程走到哪一步了”

两者刻意拆开，避免把业务流程细节全部塞进图状态。

---

## 5. 一次消息的真实执行链路

### 5.1 普通聊天链路

```text
前端发送用户消息
  -> /api/chat 或 /api/chat/stream
  -> ChatOrchestrator.load_history()
  -> set_patient_session() / set_thread_id()
  -> try_pre_route()
      -> 命中: 直接返回工具结果格式化后的回复
      -> 未命中: 构造 AgentState
  -> graph.ainvoke() / graph.astream_events()
      -> guard_in
      -> agent
           -> LLM
           -> 可选 tool_runtime 多轮工具调用
      -> guard_out 或 handoff
  -> 提取最终 AIMessage
  -> sanitize_visible_message()
  -> save_history()
  -> 返回前端
```

### 5.2 侧栏动作链路

侧栏不是一套独立 Agent。

`/api/patient/sidebar/action` 的处理方式是：

1. 前端发送结构化侧栏动作
2. 后端把动作转成一条用户消息
3. 复用 `ChatOrchestrator.run_once()`
4. 走同一套预路由 / graph / history 保存逻辑

这意味着：

- 聊天输入和侧栏操作最终收敛到同一条 agent 链路
- 修改侧栏动作语义时，必须同时关注动作消息模板和 `pre_router` 命中规则

---

## 6. 当前不是多 Agent 架构的原因

很多人看到 `LangGraph` 会默认理解成“多 Agent 工作流”，但 `patient_agent` 当前并不是。

判断依据如下：

- 只有一个真正负责 LLM 推理的 `agent` 节点
- 没有 `supervisor`、`planner`、`router agent`、`specialist agent` 等独立模型角色
- 工具不是子 Agent，而是普通工具调用
- `pre_router` 是规则判断，不是单独的模型 Agent
- `handoff` 只是固定响应节点，不参与推理

因此更准确的表述应该是：

> `patient_agent` 是单 Agent 架构，外加规则预路由和业务流程状态机。

---

## 7. 当前最重要的设计取舍

### 7.1 为什么要保留 `pre_router`

因为挂号相关动作具备以下特点：

- 语义稳定
- 目标明确
- 失败成本高
- 不适合让模型自由发挥

如果这类操作完全交给 LLM 决定，容易出现：

- 工具选择不稳定
- 重复确认
- 状态遗漏
- 回复风格与业务动作不一致

因此当前采用：

- 高频、高确定性流程走 `pre_router`
- 开放型咨询走 `agent`

### 7.2 为什么 `FlowState` 不并入 `AgentState`

因为挂号流程状态有几个特点：

- 生命周期跨多轮消息
- 与图节点跳转关系不强
- 更接近业务会话状态，而不是模型推理状态

如果强行合并：

- 图状态会快速膨胀
- 节点间耦合增加
- 未来挂号流程扩展会更难维护

所以当前拆分是合理的。

### 7.3 为什么工具循环不放在图边上

当前设计把工具循环放在 `agent` 节点内部，而不是：

```text
agent -> tool -> agent -> tool -> ...
```

这样做的好处是：

- 图更简单
- 对现阶段工具集足够用
- 不需要在图层管理过多中间节点

代价是：

- 工具执行过程更集中在 `tool_runtime.py`
- 若未来要做更复杂的可视化工作流，图层表达力会不够

---

## 8. 关键模块之间的关系

### 8.1 编排关系

```text
API
 -> ChatOrchestrator
    -> pre_router
    -> graph
       -> guard_in
       -> agent
          -> tool_runtime
             -> ALL_TOOLS
                -> HMS services
       -> guard_out / handoff
    -> RedisMemory
```

### 8.2 状态关系

```text
RedisMemory
  - 保存用户 / 助手消息历史
  - 生成线程快照

RedisFlowStateStore
  - 保存 pending_registration_confirmation
  - 保存 schedule_candidates_by_work_plan
  - 保存挂号流程相关上下文
```

### 8.3 前后端事件关系

前端消费的核心 SSE 事件包括：

- `thinking`
- `tool_start`
- `tool_end`
- `message`
- `done`

因此后端流式事件结构不能随意改名；一旦修改，前端 `App.jsx` 中的流式解析逻辑需要同步调整。

---

## 9. 当前实现中的重要边界

### 9.1 能力边界

系统当前面向的是：

- 科室查询
- 医生查询
- 排班查询
- 挂号创建
- 挂号查询
- 挂号取消
- 患者侧栏动作触发的流程引导

系统明确不应该直接承担：

- 疾病诊断
- 报告解读
- 用药建议
- 临床决策

### 9.2 合规边界

安全边界依赖两层护栏：

- `guard_in`：输入拦截高风险意图
- `guard_out`：输出补免责声明和风险修正

如果后续新增医疗相关能力，必须先评估是否会突破这两层边界。

### 9.3 架构边界

当前“Agent 架构”与“业务工作流”不是完全等价的：

- Agent 负责理解、查询、回复
- `FlowState` 负责业务流程推进

如果后续要做复杂就医工作流，不建议继续把所有流程都堆在 prompt 和 tool runtime 里。

---

## 10. 后续修改时应该改哪一层

### 10.1 新增一个高确定性业务动作

优先看：

- `app/chat/pre_router.py`
- `app/chat/flow_state.py`
- 相关工具文件

适用场景：

- “确认这个号源”
- “取消刚才那条记录”
- “查询我的某类固定信息”

判断标准：

- 用户表达稳定
- 工具调用路径明确
- 不需要复杂自然语言推理

### 10.2 新增一个开放式咨询能力

优先看：

- `app/agent/prompts.py`
- `app/agent/nodes.py`
- `app/agent/tool_runtime.py`
- 工具定义

适用场景：

- 更自然的问法理解
- 多步查询整合回答
- 查询结果解释与组织

### 10.3 修改挂号多轮流程

优先看：

- `app/chat/flow_state.py`
- `app/tools/doctor_tools.py`
- `app/tools/registration_tools.py`
- `app/chat/pre_router.py`

因为挂号流程的关键不在图，而在 **FlowState 如何沉淀和消费上下文**。

### 10.4 修改前端工具展示

优先看：

- `patient_agent_frontend/src/App.jsx`

注意：

- 当前前端工具名映射中仍存在 `query_doctor_detail`
- 但后端当前实际工具集中未必存在完全对应的实现

因此修改工具展示前，必须先对齐真实工具列表，避免前后端展示和实现继续漂移。

---

## 11. 推荐的重构方向

如果后续要继续演进，可以优先考虑下面三个方向。

### 11.1 把“挂号业务流”从隐式流程提升为显式流程

现在挂号流程主要由：

- `FlowState`
- `pre_router`
- 工具函数内部状态写入

共同完成。

后续如果流程继续复杂化，可以考虑：

- 保持单 Agent 不变
- 但把挂号确认链路抽成独立子图或显式流程模块

这样比一开始就拆成多 Agent 更稳妥。

### 11.2 强化“规则路由”和“模型路由”的分界

建议未来明确区分两类入口：

- `deterministic action`
- `agent reasoning`

这样可以减少“明明应该走规则，却绕回模型”的不稳定行为。

### 11.3 收敛工具定义与前端映射

当前工具层、前端工具展示和旧参考文档之间已经出现轻微漂移。

建议后续统一维护以下对照：

- 工具真实名称
- 工具参数契约
- 工具前端展示名
- 工具适用场景

---

## 12. 对齐时需要特别注意的几个事实

1. `patient_agent` 当前的核心不是 `graph.py`，而是 `ChatOrchestrator + pre_router + FlowState + tool_runtime`。
2. 当前不是多 Agent 架构，不要在讨论中误称为“多智能体协作”。
3. 侧栏动作不会绕过 Agent 链路，而是被转换成聊天消息后复用同一编排。
4. 状态分层是当前实现稳定性的核心，不要轻易把 `FlowState` 并回 `AgentState`。
5. 如果后续要扩展复杂业务流程，优先考虑“显式子流程”而不是直接堆 prompt。

---

## 13. 建议搭配阅读的文件

建议后续做架构对齐或修改前，至少一起阅读以下文件：

- `patient_agent_backend/app/main.py`
- `patient_agent_backend/app/chat/orchestrator.py`
- `patient_agent_backend/app/chat/pre_router.py`
- `patient_agent_backend/app/chat/flow_state.py`
- `patient_agent_backend/app/agent/graph.py`
- `patient_agent_backend/app/agent/nodes.py`
- `patient_agent_backend/app/agent/tool_runtime.py`
- `patient_agent_backend/app/tools/__init__.py`
- `patient_agent_backend/app/tools/doctor_tools.py`
- `patient_agent_backend/app/tools/registration_tools.py`
- `patient_agent_backend/app/api/patient.py`
- `patient_agent_frontend/src/App.jsx`

---

## 14. 最终结论

`patient_agent` 当前最准确的架构描述是：

> 一个以 `ChatOrchestrator` 为中心、以 `LangGraph` 单 Agent 为推理核心、以 `pre_router` 为高确定性业务旁路、以 `FlowState` 为流程状态载体、以工具层连接 HMS 的患者服务 Agent 系统。

如果后续要持续稳定演进，建议始终围绕以下原则做修改：

- 高确定性动作优先走规则
- 开放式理解交给 Agent
- 模型状态和业务流程状态分离
- 前后端事件和工具契约保持同步
- 合规边界优先于功能扩展
