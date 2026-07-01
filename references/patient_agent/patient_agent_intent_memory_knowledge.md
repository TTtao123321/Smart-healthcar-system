# patient_agent 意图识别、记忆与知识体系说明

> **文档目标**：基于当前代码实现，说明 `patient_agent` 已经具备的意图识别、记忆与知识能力边界，方便后续做需求对齐、能力评估和代码修改。
> **适用范围**：`patient_agent_backend` 当前线上/本地实现，不包含未来规划能力。
> **更新时间**：2026-06-29

---

## 1. 文档定位

这份文档不讨论“理想中的医疗 Agent 应该怎么做”，只回答 3 个现实问题：

1. 当前 agent 到底能识别哪些意图，靠什么识别？
2. 当前 agent 到底记住了什么，哪些信息会跨轮保留？
3. 当前 agent 的“知识”从哪里来，哪些内容其实并没有知识库支持？

结论先行：

- 当前没有独立的 `intent classifier`，而是 **预路由规则 + Prompt 约束 + LLM 工具选择 + 护栏规则** 的组合识别方案。
- 当前没有通用长期记忆系统，只有 **Redis 对话历史**、**Redis 线程级流程状态** 和 **患者档案表** 这三类可持久化信息。
- 当前没有 RAG / 向量知识库；所谓“知识体系”本质上由 **系统规则、HMS 实时数据、患者档案、对话上下文** 共同组成。

---

## 2. 一句话能力结论

`patient_agent` 当前更准确的能力描述是：

> 一个围绕挂号与就医信息查询场景构建的单 Agent 系统，能识别有限的高确定性业务意图、保存短期对话与挂号流程状态，并基于 Prompt 规则和 HMS 实时数据完成科室/医生/排班/挂号相关问答。

这意味着它当前擅长的是：

- 科室、诊室、楼层等医院信息查询
- 医生查询与排班查询
- 挂号创建、挂号记录查询、挂号取消
- 健康相关话题下的流程引导与免责声明补充

这也意味着它当前不具备：

- 独立可配置的意图分类体系
- 可检索的结构化医疗知识库
- 面向开放问答的长期语义记忆
- 对任意自由表达都稳定等价映射的鲁棒 NLU 能力

---

## 3. 当前意图识别体系

### 3.1 总体机制

当前意图识别不是单点实现，而是 4 层组合：

1. **Pre Router 规则直达**
   - 文件：`patient_agent_backend/app/chat/pre_router.py`
   - 作用：处理高确定性、高风险、参数补全路径明确的动作
2. **Input Guard 护栏分类**
   - 文件：`patient_agent_backend/app/guardrails/input_guard.py`
   - 作用：识别高危、诊断、报告解读、转人工、健康话题
3. **System Prompt 语义约束**
   - 文件：`patient_agent_backend/app/agent/prompts.py`
   - 作用：把常见用户语义绑定到指定工具
4. **LLM 工具选择**
   - 文件：`patient_agent_backend/app/agent/nodes.py`、`app/agent/tool_runtime.py`
   - 作用：在未命中预路由时，根据 Prompt 和上下文决定是否调用工具

因此，当前“意图识别”更像一套 **混合路由机制**，而不是一个统一的分类模型。

### 3.2 已明确实现的意图类别

### A. 预路由可稳定识别的高确定性意图

这部分不依赖 LLM，命中后直接调用工具：

- `我的挂号 / 挂号记录 / 我挂了哪些号 / 我挂的号`
  - 直接调用 `query_registration`
- `取消挂号 / 退号 / 取消这个预约 / 取消预约`
  - 先调用 `query_registration`
  - 返回记录后提示用户提供 `记录ID`
- `确认 / 就这个 / 帮我预约这个 / 帮我挂这个 / 第N个时段 / 选N`
  - 前提：当前线程里已有 `pending_registration_confirmation`
  - 直接调用 `create_registration(slot=...)`

这部分的特点是：

- 识别靠关键词与正则，不做复杂语义泛化
- 稳定性高，但覆盖范围窄
- 主要面向挂号结果确认和历史记录查询

### B. 护栏可识别的风险/边界类意图

这部分主要决定“能不能继续答”和“是否要转人工/加免责声明”：

- **高危急症**
  - 结果：直接拦截，并提示急诊/120，同时标记转人工
- **医疗诊断请求**
  - 结果：直接拒绝诊断
- **报告解读请求**
  - 结果：直接拒绝解读
- **转人工/投诉/客服诉求**
  - 结果：标记转人工
- **健康/症状话题**
  - 结果：允许继续，但标记后续需要免责声明

注意，这一层识别的是“风险边界意图”，不是业务工具意图。

### C. Prompt + LLM 可识别的业务咨询意图

当用户表达命中以下语义时，Prompt 明确要求调用对应工具：

- 科室列表、有哪些科室
  - `query_departments()`
- 某科在几楼、某科有哪些诊室
  - `query_dept_detail(dept_name=...)`
- 找医生、某科有哪些医生、某医生出诊
  - `query_doctors(...)`
- 什么时候有号、几点上班、门诊时间、排班、出诊时间
  - `query_doctor_schedules(...)`
- 我的挂号、挂号记录
  - `query_registration()`
- 取消挂号、退号
  - 先 `query_registration()`，再 `cancel_registration(...)`
- 挂号、预约、我要看病、想看某科、要看某医生
  - 进入标准挂号流程

这里的关键点是：

- 这些能力是“当前希望模型这样做”
- 真正是否稳定命中，仍受用户表达方式、Prompt 充分性、模型表现影响
- 因为没有单独分类器，所以这部分能力边界天然比预路由更模糊

### 3.3 当前意图识别的真实边界

可以把当前能力理解为 3 个层级：

- **强确定性**
  - 查询挂号、取消挂号入口、确认挂号
- **中确定性**
  - 科室/医生/排班/挂号流程咨询
- **弱确定性**
  - 复杂改写、跨句省略、模糊表达、复合指令

当前尚未实现的能力包括：

- 独立意图标签体系，例如 `query_dept`、`book_registration`、`handoff` 这样的统一枚举输出
- 统一的意图置信度
- 多意图拆解与优先级仲裁
- 基于训练数据或配置中心的语义路由
- 可回放、可评估的 NLU 标注层

也就是说，当前代码中的 `FlowState.intent` 字段存在，但并没有形成一套持续读写、驱动后续逻辑的统一意图状态机。

---

## 4. 当前记忆体系

### 4.1 总体结构

当前记忆可以分成 3 层：

1. **对话短期记忆**
   - 载体：`RedisMemory`
   - 作用：保存 thread 级 user/assistant 消息历史
2. **业务流程记忆**
   - 载体：`FlowState` + `RedisFlowStateStore`
   - 作用：保存挂号流程中跨轮需要继续消费的上下文
3. **患者资料记忆**
   - 载体：`patient_user_info` 对应的 `PatientProfile`
   - 作用：保存患者长期静态资料

这 3 层并不等价：

- `RedisMemory` 记的是“说过什么”
- `FlowState` 记的是“流程走到哪一步”
- `PatientProfile` 记的是“患者是谁、有哪些基本资料”

### 4.2 对话短期记忆

文件：

- `patient_agent_backend/app/memory/redis_memory.py`
- `patient_agent_backend/app/chat/orchestrator.py`

当前实现：

- 以 `chat:memory:{patient_id}:{thread_id}` 为 key 保存消息列表
- 默认 TTL 为 7 天
- 最多保留 `max_conversation_turns * 2` 条消息
- 同时保存线程标题、最后一条消息、更新时间、消息数等 thread 摘要

这层记忆的作用是：

- 让后续请求能恢复本线程的聊天上下文
- 让 AgentState 在新请求里重新构造 `messages`
- 支撑 `/api/chat/history` 与 `/api/chat/threads`

这层记忆的限制是：

- 只保存原始消息，不做语义摘要或知识抽取
- 超过最大轮次会裁剪旧消息
- 重心是“上下文续接”，不是“长期经验沉淀”

### 4.3 业务流程记忆

文件：

- `patient_agent_backend/app/chat/flow_state.py`
- `patient_agent_backend/app/tools/doctor_tools.py`
- `patient_agent_backend/app/tools/registration_tools.py`
- `patient_agent_backend/app/chat/pre_router.py`

`FlowState` 当前定义了这些字段：

- `intent`
- `selected_dept`
- `selected_doctor`
- `selected_date`
- `selected_work_plan_id`
- `selected_schedule_slot`
- `pending_registration_confirmation`
- `schedule_candidates_by_work_plan`

但从真实使用情况看，当前高频生效的是：

- `schedule_candidates_by_work_plan`
  - 在查排班后保存 `work_plan_id -> 医生/诊室/日期` 对应关系
- `pending_registration_confirmation`
  - 在查某个排班详情后保存待确认挂号参数和可选时段

这层记忆的核心价值是：

- 用户只说“第2个”或“就这个”时，系统还能知道在确认哪一个时段
- `create_registration(slot=...)` 可以自动补齐其余挂号参数
- `pre_router` 可以绕过 LLM 完成确认挂号

这层记忆的限制也很明确：

- 主要服务挂号流程，不是通用业务状态中心
- 成功挂号后会删除整个 thread 的 flow state
- 默认 TTL 24 小时
- 如果未正确注入 Redis store，会退回进程内内存实现，重启后丢失
- `selected_*` 与 `intent` 等字段目前更多是“预留结构”，不是完整可依赖的状态链路

### 4.4 患者资料记忆

文件：

- `patient_agent_backend/app/patient_profile/models.py`
- `patient_agent_backend/app/patient_profile/repository.py`
- `patient_agent_backend/app/patient_profile/service.py`

当前长期资料包括：

- 姓名
- 性别
- 身份证号
- 电话
- 生日
- 医保类型
- 既往史
- 过敏史
- 家族史

这层资料来源于患者档案表，不来自聊天总结。

因此它属于：

- **长期业务资料**

而不属于：

- **从聊天中自动学习得到的个性化长期记忆**

当前系统并没有把用户在对话里临时提到的偏好、常见诉求、历史问法自动沉淀成可复用记忆。

### 4.5 当前记忆体系的真实结论

当前可落地的记忆能力是：

- 记住本线程最近若干轮对话
- 记住挂号流程中的待确认上下文
- 记住患者档案中的结构化资料

当前尚未实现的记忆能力是：

- 长期语义记忆
- 对话摘要记忆
- 偏好记忆
- 跨线程统一用户画像记忆
- 基于记忆自动调整回复策略
- 通用的“上一轮提到的任何实体都能稳定引用”的强上下文消解

---

## 5. 当前知识体系

### 5.1 知识来源分层

当前知识来源可以分成 4 类：

1. **系统规则知识**
   - 来源：`SYSTEM_PROMPT`、护栏规则、预路由规则
2. **实时业务知识**
   - 来源：HMS API 返回的科室、医生、排班、挂号数据
3. **患者资料知识**
   - 来源：`PatientProfile`
4. **会话上下文知识**
   - 来源：当前 thread 的历史消息和 `FlowState`

因此当前不存在独立的“知识库服务”。

### 5.2 当前真正可依赖的知识源

### A. Prompt 规则知识

`patient_agent_backend/app/agent/prompts.py` 定义了：

- 哪些语义必须调哪些工具
- 标准挂号流程应该如何推进
- 工具返回的统一解释规则
- 医疗边界与真实性要求

这部分不是医院事实数据，但它决定了 agent 如何使用知识。

### B. HMS 实时结构化知识

当前医院事实信息主要通过工具间接获得，工具包括：

- `query_departments`
- `query_dept_detail`
- `query_doctors`
- `query_doctor_schedules`
- `query_schedule_detail`
- `create_registration`
- `query_registration`
- `cancel_registration`

这些工具背后连接的是：

- `DeptService`
- `DoctorService`
- `RegistrationService`

所以当前 agent 对“医院事实”的认知，本质上依赖 HMS 返回值，而不是模型内部知识。

### C. 患者档案知识

当前患者档案能提供的知识主要是：

- 患者基础身份信息
- 部分既往病史/过敏史/家族史

但当前这些资料更多是患者信息管理能力的一部分，不代表 agent 已经系统性使用它们进行复杂对话推理。

### D. 会话过程知识

会话历史与 FlowState 提供的是“当前上下文事实”，例如：

- 用户刚刚问的是哪个医生
- 刚查到哪个排班
- 哪个 `work_plan_id` 对应哪一天和哪个诊室
- 当前待确认的是哪个号源和哪些时段

这类知识是当前多轮挂号能够成立的关键。

### 5.3 当前知识体系不包含什么

下面这些常被误以为“已经有”，但当前实际上没有：

- 医疗知识库
- 症状到科室的系统化医学知识图谱
- 医院介绍文档的向量检索
- 医生介绍、擅长领域、评价信息的可验证知识仓
- 报告解读知识库
- 基于外部文档的检索增强生成

所以当用户问到超出 HMS 字段范围的问题时，系统只能：

- 回到工具可查范围内回答
- 给出流程性建议
- 提示咨询医生或转人工

### 5.4 当前知识体系的约束原则

当前代码已经明确把以下原则写进 Prompt 与护栏：

- 医院事实必须来自工具返回
- 不允许编造科室、医生、诊室、楼层、排班、地址、电话等信息
- 健康相关话题必须带免责声明
- 诊断、治疗、报告解读不属于可回答范围

因此当前“知识体系”的本质不是“知道很多”，而是“只允许在已验证数据范围内回答”。

---

## 6. 三套体系如何协同工作

可以把当前链路理解为：

```text
用户消息
  -> 输入护栏先判断是否高危/诊断/报告/转人工/健康话题
  -> ChatOrchestrator 尝试 pre_router 处理高确定性动作
  -> 未命中时进入单 Agent + LLM 工具选择
  -> 工具与流程上下文从 HMS / FlowState 获取结构化信息，患者资料作为独立业务资料源存在
  -> 输出护栏检查医疗建议与疑似编造
  -> 对话历史与流程状态分别写回 Redis
```

其中 3 套体系的角色分工是：

- **意图识别体系**
  - 决定走规则、走护栏还是走 LLM
- **记忆体系**
  - 决定跨轮还能保留哪些上下文
- **知识体系**
  - 决定回复能引用哪些可信事实

三者缺一不可，但当前三者都还偏“场景化实现”，不是平台化能力。

---

## 7. 当前最重要的限制

为了避免后续设计时高估现状，必须明确下面这些限制：

1. **没有统一 intent schema**
   - 当前无法稳定输出“这轮用户意图是什么”的标准标签
2. **没有通用长期记忆**
   - 当前无法把聊天中的长期偏好自动沉淀为可复用资产
3. **没有知识库检索**
   - 当前医院事实只来自 HMS，医学事实基本不提供
4. **挂号流程记忆高度中心化**
   - `FlowState` 主要为挂号设计，迁移到别的复杂流程会比较吃力
5. **意图识别对表达改写敏感**
   - 高确定性场景之外，很多行为依赖 Prompt 与模型表现
6. **患者资料虽然存在，但并未形成强对话记忆闭环**
   - 当前更像业务资料表，而不是对话智能记忆模块

---

## 8. 后续修改时建议按哪一层改

### 8.1 想增强意图识别

优先看：

- `app/chat/pre_router.py`
- `app/guardrails/input_guard.py`
- `app/agent/prompts.py`
- `app/agent/tool_runtime.py`

适合的修改方向：

- 扩展高确定性规则
- 显式引入 intent label
- 增加多意图仲裁或置信度策略

### 8.2 想增强记忆能力

优先看：

- `app/memory/redis_memory.py`
- `app/chat/flow_state.py`
- `app/chat/orchestrator.py`
- `app/patient_profile/*`

适合的修改方向：

- 对话摘要
- 更明确的流程状态机
- 跨线程用户记忆
- 患者资料与聊天上下文的融合读取

### 8.3 想增强知识体系

优先看：

- `app/agent/prompts.py`
- `app/tools/*`
- `app/hms_client/services/*`
- 如需新增知识库，再单独引入检索层

适合的修改方向：

- 扩展可查询的 HMS 字段
- 明确工具返回契约
- 引入文档检索或结构化知识库

---

## 9. 对齐结论

后续所有讨论如果要准确描述现状，建议统一使用下面这句话：

> `patient_agent` 当前已经实现的是“规则预路由 + 单 Agent 工具调用 + Redis 短期记忆 + 挂号流程状态 + HMS 实时知识”的组合能力；尚未实现统一意图分类、长期语义记忆和独立知识库检索。

如果后续文档、PRD、测试或评审中出现以下说法，需要特别谨慎：

- “系统已经有意图识别模块”
- “系统已经有长期记忆”
- “系统已经有医疗知识库”

这些表述只有在明确补齐对应实现后才成立；按当前代码，它们都只能算“局部能力”或“近似表述”，不能直接当成完整模块来使用。
