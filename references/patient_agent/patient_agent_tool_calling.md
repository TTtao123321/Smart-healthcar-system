# Patient Agent 工具调用说明

## 1. 文档目的

本文档用于说明 `patient_agent_backend` 当前的工具调用实现，方便后续做以下工作时快速对齐：

- 新增工具
- 修改工具选择规则
- 调整工具参数与返回格式
- 修改流式事件透出方式
- 排查“为什么没有调工具”或“为什么工具调错了”

本文档基于当前代码实现整理，目标是回答两个问题：

1. 工具是怎么被注册、选择和执行的
2. 后续如果要改工具调用，应该改哪些文件

---

## 2. 当前总体设计

当前项目存在两条工具调用路径：

1. **预路由直调**
   - 适用于高确定性意图
   - 不经过 LLM
   - 典型场景：`我的挂号`、`取消挂号`、`确认挂号`

2. **LLM 驱动调用**
   - 适用于普通问答、多步挂号和需要模型理解的场景
   - 由 LLM 先生成 `tool_calls`
   - 再由运行时统一执行 `tool.ainvoke(args)`

可以简化理解为：

```text
用户消息
  -> Chat API
  -> ChatOrchestrator
  -> 先尝试 PreRouter
     -> 命中则直接调工具并返回
     -> 未命中则进入 LangGraph
        -> agent 节点调用 LLM
        -> LLM 生成 tool_calls
        -> tool_runtime 执行工具
        -> LLM 基于工具结果生成最终回复
```

---

## 3. 关键文件与职责

### 3.1 入口与启动

- `patient_agent_backend/app/main.py`
  - 应用启动入口
  - 创建 `HmsClient`
  - 调用 `init_tools(hms_client)` 注册工具
  - 调用 `reset_graph()` 和 `compile_graph()` 装配并缓存 Agent 图
  - 初始化 `RedisFlowStateStore` 和 `RedisMemory`

- `patient_agent_backend/app/api/chat.py`
  - 聊天接口入口
  - `/api/chat` 对应普通请求
  - `/api/chat/stream` 对应 SSE 流式请求
  - 内部通过 `ChatOrchestrator` 驱动工具调用主流程

### 3.2 编排与执行

- `patient_agent_backend/app/chat/orchestrator.py`
  - 工具调用总编排器
  - 负责加载历史消息、设置上下文、执行预路由、执行图、保存历史
  - 流式场景下负责把 `on_tool_start` / `on_tool_end` 转成前端可消费事件

- `patient_agent_backend/app/chat/pre_router.py`
  - 高确定性意图的预路由逻辑
  - 命中规则后直接 `_invoke_tool()`，不经过 LLM

- `patient_agent_backend/app/agent/graph.py`
  - LangGraph 图定义
  - 将 `ALL_TOOLS` 绑定到 `agent` 节点

- `patient_agent_backend/app/agent/nodes.py`
  - `agent` 节点实现
  - 对 LLM 执行 `bind_tools(tools)`
  - 首次调用 LLM 后，把 `tool_calls` 交给 `run_tool_rounds()`

- `patient_agent_backend/app/agent/tool_runtime.py`
  - 工具运行时核心
  - 负责归一化 `tool_calls`
  - 负责按名称映射到真实工具并执行 `tool.ainvoke(args)`
  - 负责把工具结果重新喂给 LLM，驱动后续多轮工具调用

### 3.3 工具定义

- `patient_agent_backend/app/tools/__init__.py`
  - 工具注册中心
  - 使用 `init_tools(hms_client)` 把所有工具统一写入全局 `ALL_TOOLS`

- `patient_agent_backend/app/tools/dept_tools.py`
  - 科室相关工具

- `patient_agent_backend/app/tools/doctor_tools.py`
  - 医生与排班相关工具

- `patient_agent_backend/app/tools/registration_tools.py`
  - 挂号相关工具

### 3.4 共享上下文与状态

- `patient_agent_backend/app/agent/request_context.py`
  - 用 `ContextVar` 保存当前请求的 `patient_session` 和 `thread_id`
  - 工具内部通过这里拿到真实患者身份和线程上下文

- `patient_agent_backend/app/chat/flow_state.py`
  - 管理挂号流程中的线程级状态
  - 例如 `pending_registration_confirmation`
  - 供多轮对话中的工具共享上下文

- `patient_agent_backend/app/agent/prompts.py`
  - 系统 Prompt
  - 约束“什么语义必须调用什么工具”
  - 约束工具返回数据如何使用

---

## 4. 当前工具清单

当前代码中的工具按模块分为 3 组，共 8 个：

### 4.1 科室工具

- `query_departments`
- `query_dept_detail`

### 4.2 医生与排班工具

- `query_doctors`
- `query_doctor_schedules`
- `query_schedule_detail`

### 4.3 挂号工具

- `create_registration`
- `query_registration`
- `cancel_registration`

说明：

- 工具定义使用 `langchain_core.tools.tool` 装饰器
- 每组工具通过 `create_*_tools(hms_client)` 工厂函数创建
- `hms_client` 通过闭包注入，不依赖全局单例

---

## 5. 启动时如何注册工具

启动阶段的核心链路如下：

```text
main.py
  -> HmsClient()
  -> init_tools(hms_client)
  -> ALL_TOOLS 写入全局工具列表
  -> reset_graph()
  -> compile_graph()
```

对应职责：

- `init_tools(hms_client)` 负责收集所有工具
- `ALL_TOOLS` 是后续预路由和 LangGraph 共用的统一工具池
- `reset_graph()` 的作用是防止工具变更后仍复用旧图缓存
- `compile_graph()` 会重新构造带最新工具列表的可执行图

这意味着：

- **只写了工具函数但没有在 `init_tools()` 中注册，系统不会调用到**
- **改了工具定义后如果不重置图缓存，可能仍然使用旧绑定**

---

## 6. 请求时的完整调用链

### 6.1 普通请求

```text
/api/chat
  -> ChatOrchestrator.run_once()
  -> set_patient_session(session)
  -> set_thread_id(thread_id)
  -> load history
  -> try_pre_route()
     -> 命中：直接执行工具并返回
     -> 未命中：进入 graph.ainvoke(state)
        -> guard_in
        -> agent
           -> LLM 生成 tool_calls
           -> run_tool_rounds()
              -> tool.ainvoke(args)
              -> 结果回灌 LLM
           -> 得到最终 AI 回复
        -> guard_out
  -> save history
  -> 返回前端
```

### 6.2 流式请求

```text
/api/chat/stream
  -> ChatOrchestrator.run_stream()
  -> try_pre_route()
     -> 命中：直接返回 message/done
     -> 未命中：graph.astream_events(...)
        -> on_chat_model_stream
        -> on_tool_start
        -> on_tool_end / on_tool_error
        -> on_chain_end
  -> orchestrator 转换为 SSE 事件
```

---

## 7. 预路由是怎么工作的

预路由位于 `app/chat/pre_router.py`，它的定位是：

- 用规则直接处理高置信意图
- 避免模型在简单场景下重复推理
- 提高稳定性和响应速度

当前主要规则包括：

- 查询挂号：命中 `我的挂号`、`挂号记录` 等语义后，直接调用 `query_registration`
- 取消挂号：命中 `取消挂号`、`退号` 等语义后，先调用 `query_registration` 返回可选记录
- 确认挂号：当 `flow_state.pending_registration_confirmation` 存在时，命中 `确认`、`就这个`、`第 N 个时段` 等语义后，直接调用 `create_registration`

预路由内部真实执行工具的地方是：

```python
return await tool.ainvoke(args)
```

这里的特点是：

- 不依赖 LLM 输出的 `tool_calls`
- 参数由预路由逻辑自己构造
- 返回结果会被格式化成用户可读文案后直接返回

适合放到预路由的场景：

- 规则非常稳定
- 意图识别成本低
- 返回格式可控
- 不需要模型继续做复杂推理

不适合放到预路由的场景：

- 需要跨多个工具决策
- 需要理解用户模糊表达
- 需要模型基于工具结果继续追问或总结

---

## 8. LLM 驱动调用是怎么工作的

### 8.1 工具绑定

`app/agent/nodes.py` 中通过：

```python
base_llm.bind_tools(tools)
```

把工具描述绑定给 LLM。这里的含义是：

- 模型知道有哪些工具可以用
- 模型知道每个工具的名字、参数和描述
- 模型在推理后可以输出标准 `tool_calls`

需要注意：

- `bind_tools()` 只是“让模型知道工具”，**不是执行工具**
- 真正执行依然在运行时 `run_tool_rounds()` 中完成

### 8.2 首次模型调用

`agent()` 节点会：

1. 构造 `[SystemMessage] + 历史消息 + 当前用户消息`
2. 调用 `llm.ainvoke(llm_messages)`
3. 如果返回中包含 `tool_calls`，就进入 `run_tool_rounds()`

### 8.3 工具循环执行

`run_tool_rounds()` 的逻辑可以概括为：

```text
拿到 AIMessage.tool_calls
  -> normalize_tool_calls()
  -> 逐个查找 tool_map[tool_name]
  -> 执行 await tool.ainvoke(tool_args)
  -> 把工具结果包装成消息追加到 llm_messages
  -> 追加 TOOL_FOLLOWUP_PROMPT
  -> 再次 llm.ainvoke(llm_messages)
  -> 若仍有 tool_calls，继续下一轮
```

这个循环最多执行 `MAX_TOOL_ROUNDS = 5` 轮，避免模型无限调用工具。

### 8.4 空工具名回退

`tool_runtime.py` 中还实现了 `recover_tool_call()` 和 `normalize_tool_calls()`，用于处理模型输出异常：

- 如果模型给了空工具名
- 但用户语义明显命中某类工具
- 系统会按关键词做有限回退

当前已覆盖的回退示例：

- `有哪些科室` -> `query_departments`
- `我的挂号` -> `query_registration`
- `哪些医生` / `找医生` -> `query_doctors`

这属于兜底机制，不应替代正常的 Prompt 和工具定义。

---

## 9. 工具内部怎么拿上下文

当前项目刻意不让模型直接传入 `patient_id`，而是由工具内部读取当前请求上下文：

```python
patient_id = get_patient_id()
thread_id = get_thread_id()
```

这样做的目的：

- 避免模型伪造患者身份
- 确保工具始终操作当前登录患者
- 让工具签名更聚焦业务参数，而不是安全上下文参数

例如挂号工具中：

- `query_registration()` 会基于当前登录患者查询挂号记录
- `cancel_registration()` 会先校验记录是否属于当前患者
- `create_registration()` 会结合 `thread_id` 到 `FlowStateStore` 中读取待确认挂号状态

这部分是工具调用安全性的关键，不建议改成“由模型直接传患者 ID”。

---

## 10. Flow State 在工具调用中的作用

`app/chat/flow_state.py` 保存的是线程级状态，不是全局状态。

当前工具调用最依赖它的场景是挂号确认：

1. 前面步骤已查询排班和时段
2. 系统把待确认信息写入 `pending_registration_confirmation`
3. 用户回复 `确认` 或 `第 2 个时段`
4. `create_registration(slot=...)` 从 flow state 自动补齐：
   - `work_plan_id`
   - `doctor_schedule_id`
   - `doctor_id`
   - `dept_sub_id`
   - `appointment_date`

因此：

- Flow State 让多轮挂号对话成为可能
- 工具可以只接收用户当前确认的最小信息
- 但前提是上游步骤必须已经把状态写全

如果后续出现“确认挂号时报参数缺失”，优先检查：

- 上游是否正确写入 `pending_registration_confirmation`
- `thread_id` 是否在当前请求中正确设置
- 工具是否从正确的 thread key 加载状态

---

## 11. 流式工具事件如何透出给前端

在流式接口中，前端之所以能看到工具调用过程，不是因为工具主动发事件，而是因为：

1. `graph.astream_events(..., version="v2")` 会产生图执行事件
2. `ChatOrchestrator.run_stream()` 消费这些事件
3. 命中 `on_tool_start` / `on_tool_end` / `on_tool_error` 时，转换成 SSE 事件输出

当前对前端暴露的工具相关事件包括：

- `tool_start`
  - `tool_call_id`
  - `tool_name`
  - `tool_args`

- `tool_end`
  - 成功时包含 `tool_result`
  - 失败时包含 `tool_error`

如果后续要改前端工具调试面板，优先检查：

- `app/chat/orchestrator.py` 的 `run_stream()`
- 前端对 SSE 事件名和字段名的消费逻辑

---

## 12. 当前约束与不变式

后续改工具调用时，建议默认遵守以下约束：

### 12.1 统一返回格式

所有工具应保持统一 JSON 字符串返回：

- 成功且有数据：`{"ok": true, "summary": "...", "data": [...] 或 {...}}`
- 成功但无数据：`{"ok": true, "summary": "...", "data": [], "hint": "..."}`
- 失败：`{"ok": false, "error": "...", "hint": "..."}`

原因：

- Prompt 已按这一格式约束模型解读工具结果
- `classify_tool_result()` 依赖这一结构做降级分类
- 预路由格式化逻辑也依赖这一结构

### 12.2 患者身份来自上下文

- 不要把 `patient_id` 暴露为模型可自由填写的业务参数
- 工具内部通过 `request_context` 获取真实身份

### 12.3 图和工具注册要同步

- 新增或删除工具后，要确认 `init_tools()` 是否同步更新
- 变更工具描述、参数或数量后，要注意图缓存是否已重置

### 12.4 Prompt、预路由、运行时三者要一致

工具调用正确与否，不只取决于工具函数本身，还依赖三层一致性：

1. Prompt 是否把语义映射到正确工具
2. PreRouter 是否覆盖了应当直调的高确定性场景
3. Tool Runtime 是否能正确识别和执行 `tool_calls`

---

## 13. 后续修改时应该改哪里

### 13.1 新增一个工具

至少要检查这些位置：

1. `app/tools/*.py`
   - 新增工具函数
2. `app/tools/__init__.py`
   - 注册到 `ALL_TOOLS`
3. `app/agent/prompts.py`
   - 增加触发语义与调用规则
4. `app/chat/pre_router.py`
   - 判断该工具是否适合做预路由直调
5. 前端流式面板或日志分析逻辑
   - 如需展示新工具名，确认消费逻辑是否依赖白名单

### 13.2 修改工具参数

优先检查：

- 工具签名和 docstring
- Prompt 中是否仍使用旧参数语义
- Flow State 是否还在写入/读取旧字段
- PreRouter 是否还在构造旧参数
- 前端或日志中是否展示旧字段名

### 13.3 修改工具返回结构

高风险，必须同步检查：

- `app/agent/prompts.py`
- `app/agent/tool_runtime.py` 中的 `classify_tool_result()`
- `app/chat/pre_router.py` 中的 `_parse_tool_result()` 和 `_format_tool_message()`

### 13.4 把某个场景从 LLM 路由改成预路由

需要评估：

- 语义是否足够稳定
- 是否需要多步决策
- 是否会影响后续 Flow State

落地时通常要改：

- `app/chat/pre_router.py`
- `app/agent/prompts.py`

### 13.5 排查“模型没有调工具”

按下面顺序排查最有效：

1. `app/agent/prompts.py`
   - 语义触发规则是否足够明确
2. 工具是否已在 `init_tools()` 注册
3. `bind_tools()` 是否绑定到最新工具列表
4. 模型输出中是否出现空工具名
5. `normalize_tool_calls()` 是否把异常输出过滤掉了
6. 用户请求是否其实已被预路由提前拦截

---

## 14. 建议的对齐清单

每次改工具调用前后，建议至少对齐以下内容：

### 14.1 代码层

- 工具函数名称是否唯一且语义稳定
- 参数名是否与 Prompt 描述一致
- 返回结构是否仍满足统一约束
- Flow State 字段名是否前后一致

### 14.2 交互层

- 普通请求路径是否能走通
- 流式请求是否仍能正确输出 `tool_start` / `tool_end`
- 预路由和图内调用是否没有冲突

### 14.3 日志层

- 是否仍能看到 `tool_call_start`
- 是否仍能看到 `tool_call_end`
- `route_type` 是否能区分 `pre_route` 和 `graph_route`
- `degraded` 和 `error_type` 是否仍可用于排障

---

## 15. 一个典型示例

### 15.1 “我的挂号”

调用路径：

```text
用户: 我的挂号
  -> chat.py
  -> orchestrator.run_once()
  -> try_pre_route()
  -> _invoke_tool("query_registration", {})
  -> query_registration() 从 request_context 读取 patient_id
  -> 调用 hms_client.registration_service.query(...)
  -> 格式化结果
  -> 返回用户
```

特点：

- 不经过 LLM
- 速度快
- 风险低
- 返回结构更可控

### 15.2 “心内科王医生明天还有号吗”

调用路径：

```text
用户: 心内科王医生明天还有号吗
  -> chat.py
  -> orchestrator.run_once()
  -> try_pre_route() 未命中
  -> graph.ainvoke(state)
  -> agent()
  -> llm.ainvoke()
  -> 生成 query_doctor_schedules(...) 等 tool_calls
  -> run_tool_rounds()
  -> tool.ainvoke(args)
  -> 工具结果回灌 LLM
  -> 输出最终自然语言回复
```

特点：

- 依赖 Prompt 和工具描述
- 适合复杂语义理解
- 支持多步工具链

---

## 16. 推荐维护原则

为了让后续修改成本更低，建议遵循以下原则：

- **优先保持工具签名稳定**
  - 避免频繁改工具名和核心参数名

- **优先把稳定规则放到预路由**
  - 对高确定性意图，规则直调通常比模型调用更稳

- **优先把业务状态放在线程级 Flow State**
  - 不要依赖模型“记住”上一轮工具结果里的关键参数

- **优先保证 Prompt、PreRouter、Tool Runtime 三处一致**
  - 任何一处单改，都可能导致工具调用偏移

- **优先保持返回结构统一**
  - 统一格式是当前模型解读、预路由格式化和日志归因的共同基础

---

## 17. 后续可补充项

如果后续希望把这份文档继续升级，建议补充两类内容：

1. **工具级时序图**
   - 分别画 `query_registration`
   - `query_doctor_schedules`
   - `create_registration`

2. **变更案例记录**
   - 每次改工具参数或路由策略时，补一条“修改原因 / 影响范围 / 验证结果”

这样后续做功能对齐、测试回归和问题归因会更快。
