# patient_agent 多轮对话现状说明

> **文档目标**：基于当前代码实现，说明 `patient_agent` 目前真实可实现的多轮对话能力、状态依赖、能力边界和修改入口，方便后续对齐、重构和扩展。
> **适用范围**：`patient_agent_backend` 当前聊天链路、挂号流程链路，以及与多轮对话直接相关的状态与工具。
> **更新时间**：2026-06-29

---

## 1. 文档定位

这份文档聚焦的是 **“当前 agent 已经能稳定实现的多轮对话”**，不是理想形态，也不是未来设计稿。

重点回答 5 个问题：

1. 当前多轮对话到底靠什么实现？
2. 现在已经支持哪些多轮场景？
3. 哪些状态字段是真正在用，哪些只是预留？
4. 当前多轮能力的边界在哪里？
5. 如果后续要改多轮行为，应该优先改哪些文件？

结论先行：

- 当前 `patient_agent` 已实现 **基于 `patient_id + thread_id` 的多轮历史记忆**。
- 当前 `patient_agent` 已实现 **围绕挂号流程的线程级业务状态持久化**。
- 当前真正稳定的多轮状态机主要集中在 **挂号确认链路**，不是通用的“全场景 slot filling 系统”。
- 当前多轮能力由 `ChatOrchestrator + RedisMemory + FlowState + pre_router + tools` 共同完成，不是只靠 `LangGraph` 图本身。

---

## 2. 一句话结论

`patient_agent` 当前的多轮对话实现，本质上是：

> 一套以 `thread_id` 为线程标识、以 Redis 历史消息为上下文记忆、以 `FlowState` 保存挂号流程状态、以 `pre_router` 和工具层推进高确定性业务动作的单 Agent 多轮对话体系。

这句话里有 4 个关键词：

- **历史记忆**
  - 解决“模型能看到前面聊过什么”
- **线程状态**
  - 解决“挂号流程当前推进到哪一步”
- **规则旁路**
  - 解决“确认挂号、查挂号这类高确定性动作要更稳”
- **工具执行**
  - 解决“医院真实数据必须来自 HMS，而不是模型编造”

---

## 3. 当前多轮对话依赖的核心组件

### 3.1 对话历史：`RedisMemory`

职责：

- 按 `patient_id + thread_id` 读取历史消息
- 在一次回复结束后保存本轮用户消息和助手消息
- 支持线程列表与线程删除

它解决的是：

- “上一轮说过什么”
- “当前这条消息属于哪个会话线程”
- “同一个患者能不能打开多个独立聊天线程”

当前特点：

- 历史消息是 **通用对话上下文**
- 生命周期默认比流程状态更长
- 对所有聊天场景都生效，不只限于挂号

### 3.2 流程状态：`FlowState`

职责：

- 保存挂号流程中的线程级业务上下文
- 跨多轮共享候选排班和待确认挂号信息

它解决的是：

- “刚才查到的时段是哪几个”
- “用户现在说的‘就这个’指的是哪个号源”
- “创建挂号时需要的参数能不能从前文自动补齐”

当前特点：

- `FlowState` 不是聊天消息历史
- `FlowState` 不是通用意图引擎
- `FlowState` 当前主要服务 **挂号确认链路**

### 3.3 编排入口：`ChatOrchestrator`

职责：

1. 加载历史消息
2. 设置当前 `patient_session` 和 `thread_id`
3. 先尝试 `pre_router`
4. 未命中时再走 `LangGraph`
5. 回写历史消息

这意味着当前多轮对话不是“模型自己记住流程”，而是：

- 历史由记忆层提供
- 流程由状态层保存
- 高确定性动作由规则层推进
- 开放式理解由 Agent 完成

### 3.4 规则预路由：`pre_router`

职责：

- 对高确定性表达直接命中工具
- 减少“本来应当稳定执行，却交给模型自由发挥”的不稳定性

当前和多轮强相关的预路由场景主要有：

- 查询我的挂号
- 取消挂号前先列出可选记录
- 在待确认挂号状态存在时，处理“确认”“就这个”“第 2 个时段”之类的确认表达

### 3.5 工具层：`dept_tools` / `doctor_tools` / `registration_tools`

职责：

- 连接 HMS 真实数据
- 在关键节点写入或读取 `FlowState`
- 把多轮对话里的省略信息自动补齐

当前多轮最关键的工具状态写入点有两个：

- `query_doctor_schedules`
  - 写入候选排班缓存
- `query_schedule_detail`
  - 写入待确认挂号上下文

创建挂号时，`create_registration` 会读取这些状态完成参数补齐。

---

## 4. 当前真实支持的多轮对话能力

## 4.1 通用历史续聊

当前系统已支持：

- 同一 `thread_id` 下连续多轮对话
- 下一轮消息带上前文历史进入模型上下文
- 同一患者维护多个线程
- 恢复历史后继续提问

适用场景：

- 连续咨询同一问题
- 在前面问过医生或科室后，继续追问
- 中断后重新进入同一线程继续聊

需要注意：

- 这类“续聊”主要依赖历史消息，不一定依赖 `FlowState`
- 是否能正确理解“他”“这个医生”“刚才那个科室”这类指代，更多取决于模型和上下文，不是显式状态机保证

也就是说：

- **系统支持多轮上下文续聊**
- **但不是所有省略表达都由显式槽位系统稳定兜底**

## 4.2 挂号流程多轮确认

这是当前实现里最明确、最稳定的多轮场景。

典型流程如下：

1. 用户先查询某科室某医生某天是否有号
2. 系统调用排班查询工具，拿到候选时段
3. 用户继续查看某个具体排班详情
4. 系统把待确认挂号信息写入 `pending_registration_confirmation`
5. 用户回复“确认”“就这个”“第 2 个时段”
6. 系统根据当前线程中的 `FlowState` 自动补齐创建挂号参数
7. 调用 `create_registration`

这条链路说明了一个关键事实：

- 当前挂号不是每轮都要求用户重新输入完整参数
- 系统已经能把前面轮次查到的结构化结果沉淀为线程级状态
- 最终通过状态补齐完成创建挂号

这是当前最接近“业务状态机”的实现部分。

## 4.3 查挂号与取消挂号引导

当前系统已支持：

- 用户直接说“我的挂号”
- 系统通过预路由直接调用 `query_registration`
- 用户说“取消挂号”
- 系统先列出当前患者名下可取消或可查看的挂号记录，再由后续轮次继续选择

这里的特点是：

- 这条链路属于 **规则主导的多轮引导**
- 它不依赖复杂模型推理
- 稳定性主要来自 `pre_router` 和挂号工具本身

## 4.4 侧栏动作转多轮对话

当前系统已支持患者侧栏动作复用同一套聊天链路：

- 前端把结构化侧栏动作发送到后端
- 后端把动作转成一条 JSON 文本消息
- 仍然进入 `ChatOrchestrator.run_once()`
- 继续复用相同的历史、预路由、图执行和工具调用逻辑

这意味着：

- 侧栏触发的流程也能接在同一个线程上下文后面继续聊
- 多轮对话的“入口”不只来自自由文本，也可以来自结构化 UI 动作

---

## 5. 当前多轮能力的状态模型

## 5.1 `AgentState` 和 `FlowState` 是两层状态

### A. `AgentState`

定位：

- LangGraph 图执行时的运行态

当前字段包括：

- `messages`
- `patient_id`
- `guardrail_result`
- `needs_handoff`
- `disclaimer_shown`
- `conversation_turn`

它解决的是：

- 本次图执行需要哪些输入和控制字段

它不负责：

- 长周期挂号流程沉淀
- 通用业务槽位管理

### B. `FlowState`

定位：

- 线程级业务流程状态

定义字段包括：

- `intent`
- `selected_dept`
- `selected_doctor`
- `selected_date`
- `selected_work_plan_id`
- `selected_schedule_slot`
- `pending_registration_confirmation`
- `schedule_candidates_by_work_plan`

但必须特别注意：

> 这些字段“被定义”不等于“都在当前业务里真实被使用”。

## 5.2 当前真实在用的 `FlowState` 字段

根据当前代码检索结果，实际被明确读写并影响业务行为的核心字段主要是：

- `pending_registration_confirmation`
  - 保存待确认挂号上下文
  - 创建挂号时用于补齐参数
- `schedule_candidates_by_work_plan`
  - 保存排班候选缓存
  - 供排班详情与后续确认链路使用

这两个字段是当前多轮挂号链路真正落地的状态核心。

## 5.3 当前更偏“预留字段”的部分

虽然 `FlowState` 中还定义了这些字段：

- `intent`
- `selected_dept`
- `selected_doctor`
- `selected_date`
- `selected_work_plan_id`
- `selected_schedule_slot`

但按当前代码检索结果，它们暂时没有形成明确、稳定的业务读写闭环。

这意味着：

- 当前系统 **不是一个完整通用槽位系统**
- 当前系统 **没有把所有多轮理解都显式落到 slot 上**
- 当前实现的重点在“挂号确认所需状态最小闭环”，而不是“大一统流程状态机”

---

## 6. 当前多轮对话的真实执行链路

### 6.1 普通多轮聊天链路

```text
用户发送消息
  -> /api/chat 或 /api/chat/stream
  -> require_patient_session 校验患者会话
  -> ChatOrchestrator.load_history()
  -> set_patient_session()
  -> set_thread_id()
  -> try_pre_route()
       -> 命中：直接调用工具并返回
       -> 未命中：构造 AgentState
  -> graph.ainvoke() / graph.astream_events()
       -> guard_in
       -> agent
            -> LLM
            -> run_tool_rounds()
       -> guard_out 或 handoff
  -> sanitize_visible_message()
  -> save_history()
  -> 返回前端
```

### 6.2 挂号确认多轮链路

```text
用户查询医生或排班
  -> 查询工具返回候选号源
  -> FlowState 写入 schedule_candidates_by_work_plan

用户查看具体排班详情
  -> query_schedule_detail
  -> FlowState 写入 pending_registration_confirmation

用户回复“确认 / 就这个 / 第2个时段”
  -> pre_router 检测当前线程存在 pending_registration_confirmation
  -> create_registration(slot=...)
  -> 工具从 FlowState 自动补齐参数
  -> 创建成功后清理对应线程状态
```

这条链路是当前最明确的“多轮状态推进”实现。

---

## 7. 当前可稳定对齐的多轮场景

为了后续对齐方便，可以把当前系统支持的多轮场景归为 4 类。

### 7.1 历史续聊型

定义：

- 依赖历史消息上下文续问
- 不依赖显式业务状态机

示例：

- “刚才说的心内科还有别的医生吗”
- “那这个医生明天下午呢”

特点：

- 有能力支持
- 但稳定性主要受模型上下文理解影响
- 不属于严格可控的流程状态推进

### 7.2 查询后确认型

定义：

- 前一轮查询结果为后一轮动作提供结构化上下文

示例：

- “帮我看看王医生明天有没有号”
- “看第二个时段”
- “确认挂这个”

特点：

- 这是当前最成熟的多轮模式
- 依赖 `FlowState`
- 稳定性高于纯模型续聊

### 7.3 规则引导型

定义：

- 对高确定性表达走预路由
- 多轮主要由规则和工具推进

示例：

- “我的挂号”
- “取消挂号”
- “就取消第一条”

特点：

- 对业务动作更稳
- 路由和文案更可控
- 后续最适合继续扩展为显式规则流程

### 7.4 侧栏动作衔接型

定义：

- UI 结构化动作进入同一聊天线程

示例：

- 从侧栏点击某个患者动作后，系统自动发出一条动作消息
- 用户继续在聊天框追问

特点：

- 侧栏不是独立流程引擎
- 本质上仍然接到同一套多轮聊天链路

---

## 8. 当前多轮能力的边界

## 8.1 当前不是通用对话状态机

虽然已经有多轮能力，但当前系统 **不是** 下列形态：

- 不是全场景统一意图管理器
- 不是完整的 slot-filling 引擎
- 不是所有问法都能显式落到结构化状态
- 不是多 Agent 协作式流程编排

更准确的说法是：

- 对话历史是通用的
- 挂号状态是局部显式的
- 其余场景大多仍靠模型基于历史理解

## 8.2 当前多轮显式状态主要服务挂号

当前 `FlowState` 的真实闭环主要集中在：

- 排班候选缓存
- 待确认挂号信息
- 创建挂号参数补齐

这意味着如果后续要扩展：

- “复诊随访多轮收集”
- “就诊偏好多轮澄清”
- “症状问诊多轮结构化采集”

都不能默认认为当前状态体系已经天然支持。

## 8.3 创建挂号存在强前置条件

当前 `create_registration` 的约束很明确：

- 不是只要参数齐全就能随便创建
- 当前线程里必须已有 `pending_registration_confirmation`
- 且请求上下文中必须能取到当前患者和线程信息

这保证了安全性和流程一致性，但也意味着：

- 不能绕过前置查询链路直接做任意挂号创建
- 修改这条规则会直接影响系统的流程安全边界

## 8.4 `intent` 当前不是主驱动字段

虽然 `FlowState` 里有 `intent` 字段，但当前未形成明确的业务驱动闭环。

所以后续讨论时要避免误判：

- 不要把当前系统描述成“已有完善意图状态机”
- 不要默认“新增一个场景只要给 intent 加枚举即可”

当前更接近：

- Prompt 规则
- `pre_router` 模式匹配
- 工具运行时关键词兜底

共同构成了现有的路由机制。

## 8.5 合规边界依然优先于多轮能力

当前对医疗高风险话题仍有明确护栏：

- 输入侧可拦截高危、诊断、报告解读类请求
- 输出侧会补免责声明或做风险修正

因此多轮能力并不意味着系统会无限制地进入医疗建议或诊断流程。

---

## 9. 后续修改多轮行为时应该优先改哪里

## 9.1 想改“高确定性多轮业务动作”

优先检查：

- `patient_agent_backend/app/chat/pre_router.py`
- `patient_agent_backend/app/chat/flow_state.py`
- `patient_agent_backend/app/tools/doctor_tools.py`
- `patient_agent_backend/app/tools/registration_tools.py`

适用场景：

- 新增确认表达
- 调整“第 N 个时段”的选择逻辑
- 增加挂号前二次确认
- 让取消挂号支持更多轮的记录选择

## 9.2 想改“开放式续聊理解”

优先检查：

- `patient_agent_backend/app/agent/prompts.py`
- `patient_agent_backend/app/agent/nodes.py`
- `patient_agent_backend/app/agent/tool_runtime.py`
- 对应工具定义

适用场景：

- 更自然地理解“刚才那个医生”
- 更稳定地从历史中承接上下文
- 更准确地选择工具

## 9.3 想新增一个显式多轮状态字段

优先检查：

- `patient_agent_backend/app/chat/flow_state.py`
- 写入该状态的工具或预路由逻辑
- 消费该状态的工具或预路由逻辑
- 相关测试

必须注意：

- 只“定义字段”没有意义
- 必须同时设计“谁写入、谁读取、何时清理”
- 否则状态只会变成名义上的预留字段

## 9.4 想修改多轮流式展示

优先检查：

- `patient_agent_backend/app/chat/orchestrator.py`
- 前端 SSE 消费逻辑

尤其是以下事件：

- `thinking`
- `tool_start`
- `tool_end`
- `message`
- `done`

因为这些事件决定了前端如何把多轮中的思考和工具调用过程展示给用户。

---

## 10. 建议的对齐方式

为了避免后续讨论时把“理想能力”和“现有能力”混在一起，建议统一按下面 4 个层次对齐。

### 10.1 历史记忆层

确认问题：

- 这个场景是否只需要依赖聊天历史？
- 如果仅靠历史，模型是否能稳定承接？

### 10.2 显式状态层

确认问题：

- 这个场景是否需要跨轮保存结构化上下文？
- 状态字段由谁写入、谁消费、何时清理？

### 10.3 规则路由层

确认问题：

- 这个场景是否属于高确定性动作？
- 是否应优先走 `pre_router`，而不是交给模型自由判断？

### 10.4 工具契约层

确认问题：

- 真正依赖的医院数据来自哪个工具？
- 返回结构是否能支撑后续多轮动作？

只有这 4 层同时清楚，才能判断一个“多轮需求”到底是：

- 只改 prompt 就够
- 需要补状态字段
- 需要加预路由
- 还是必须新增工具能力

---

## 11. 推荐阅读顺序

如果后续要修改当前多轮对话，建议按下面顺序阅读代码：

1. `patient_agent_backend/app/api/chat.py`
2. `patient_agent_backend/app/chat/orchestrator.py`
3. `patient_agent_backend/app/chat/pre_router.py`
4. `patient_agent_backend/app/chat/flow_state.py`
5. `patient_agent_backend/app/agent/state.py`
6. `patient_agent_backend/app/agent/graph.py`
7. `patient_agent_backend/app/agent/nodes.py`
8. `patient_agent_backend/app/agent/tool_runtime.py`
9. `patient_agent_backend/app/tools/doctor_tools.py`
10. `patient_agent_backend/app/tools/registration_tools.py`
11. `patient_agent_backend/app/memory/redis_memory.py`
12. `patient_agent_backend/app/patient_sidebar/actions.py`

建议搭配关注的测试包括：

- `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`
- `patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py`
- `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`
- `patient_agent_backend/tests/test_tools/test_registration_flow_state.py`

---

## 12. 最终结论

当前 `patient_agent` 的多轮对话能力可以准确概括为：

> 系统已经具备通用历史续聊能力，并在挂号流程上实现了较完整的线程级显式状态闭环；其中最稳定的多轮行为集中在“查询排班 -> 查看详情 -> 确认挂号 -> 创建挂号”这一链路，而其余场景仍主要依赖历史消息和模型理解，不应误判为已经拥有完整通用的意图槽位系统。

因此，后续如果要继续演进，建议始终先分清 3 件事：

- 这是“历史续聊问题”，还是“业务流程状态问题”
- 这是“高确定性动作”，还是“开放式自然语言理解”
- 这是“补 prompt 就够”，还是“必须补 `FlowState` + `pre_router` + 工具闭环”

只有先把这三件事讲清楚，后续对齐和修改才不会继续漂移。
