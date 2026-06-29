# Patient Agent 改造优先级进度对照

**日期**: 2026-06-28
**适用范围**: `patient_agent_backend` 本轮稳定性与可靠性改造
**对照口径**: 本文对应的是本次会话中整理的“改造优先级清单”，不是 PRD 或产品路线图中的功能分期 `P0-P3`

---

## 1. 总览

- `P0`: 已完成
- `P1`: 已完成
- `P2`: 未完成
- `P3`: 未完成

一句话总结:

- 本轮实际落地的是 `P0 + P1`
- `P2 + P3` 没有进入实施范围

---

## 2. P0 进度

### 2.1 目标

P0 的目标是先稳住挂号主链路，降低强流程场景对模型首轮决策的依赖，并保证线程级状态在服务重启或多实例场景下不丢失。

### 2.2 已完成项

- [x] `FlowState Redis 化`
  - 已将线程级挂号确认状态从进程内内存迁移到 Redis
  - 已支持 `chat:flow-state:{patient_id}:{thread_id}` 的 key 规则与 TTL
  - 对应文件:
    - `patient_agent_backend/app/chat/flow_state.py`
    - `patient_agent_backend/app/config/settings.py`
    - `patient_agent_backend/tests/test_memory/test_flow_state_store.py`

- [x] 启动时默认注入 Redis `FlowStateStore`
  - 应用启动时已创建并注入 Redis store，而不是继续依赖默认内存实现
  - 对应文件:
    - `patient_agent_backend/app/main.py`
    - `patient_agent_backend/tests/test_api/test_main_flow_state_store.py`

- [x] 高频强流程前置路由
  - 已对以下高确定性请求增加前置路由:
    - 查询挂号记录
    - 取消挂号路径
    - 存在待确认挂号状态时的确认挂号路径
  - 对应文件:
    - `patient_agent_backend/app/chat/pre_router.py`
    - `patient_agent_backend/app/chat/orchestrator.py`
    - `patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py`

- [x] 主链路回归测试补齐
  - 已补充 Redis store、前置路由、挂号确认态、挂号链路集成回归
  - 对应文件:
    - `patient_agent_backend/tests/test_tools/test_registration_flow_state.py`
    - `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`
    - `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`
    - `patient_agent_backend/tests/test_api/test_chat_orchestrator.py`

### 2.3 当前可对照结论

- 挂号确认链路不再只依赖进程内内存
- 高频主链路不再完全依赖模型首轮自行挑工具
- 本轮稳定性改造的基础闭环已经建立

### 2.4 未完成项

- [ ] 无

说明:

- 按本次“改造优先级清单”的定义，P0 已完成，没有遗留待办

---

## 3. P1 进度

### 3.1 目标

P1 的目标是在不重写整体 LangGraph 架构的前提下，收口工具运行时职责，补齐最小必要的错误分级和关键日志，并保证前端现有 SSE 协议兼容。

### 3.2 已完成项

- [x] 工具运行时辅助层抽离
  - 已将工具调用循环、工具名回退、工具结果解析、多轮调用控制等逻辑从 `nodes.py` 收口到独立运行时文件
  - 对应文件:
    - `patient_agent_backend/app/agent/tool_runtime.py`
    - `patient_agent_backend/app/agent/nodes.py`
    - `patient_agent_backend/tests/test_agent/test_tool_runtime.py`

- [x] 最小必要错误分级
  - 已形成本轮改造所需的最小错误分级集合:
    - `validation_error`
    - `empty_result`
    - `upstream_error`
    - `runtime_error`
  - 对应文件:
    - `patient_agent_backend/app/agent/tool_runtime.py`
    - `patient_agent_backend/tests/test_logging/test_patient_agent_route_logging.py`

- [x] 关键链路结构化日志
  - 已覆盖:
    - `route_type`
    - `error_type`
    - `degraded`
    - 相关工具调用关键字段
  - 对应文件:
    - `patient_agent_backend/tests/test_logging/test_patient_agent_route_logging.py`
    - `patient_agent_backend/app/chat/pre_router.py`
    - `patient_agent_backend/app/chat/orchestrator.py`
    - `patient_agent_backend/app/agent/tool_runtime.py`

- [x] SSE 协议兼容下的稳定性补修
  - 已修复流式最终回复中暴露 `think:`、协议行、工具噪声的问题
  - 已修复自然语言预约 `doctor-only` 场景下的排班查询问题
  - 对应文件:
    - `patient_agent_backend/app/chat/orchestrator.py`
    - `patient_agent_backend/app/chat/output_filters.py`
    - `patient_agent_backend/app/tools/doctor_tools.py`
    - `patient_agent_backend/tests/test_guardrails/test_chat_output_filters.py`
    - `patient_agent_backend/tests/test_api/test_chat_stream_api.py`
    - `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`

### 3.3 当前可对照结论

- `nodes.py` 的运行时职责已明显收口
- 工具调用异常、空结果、上游失败不再是完全混在一起的黑盒
- 流式最终用户可见消息已经从“协议残片混入”恢复到“只展示结果文本”

### 3.4 未完成项

- [ ] 无

说明:

- 按本次“改造优先级清单”的定义，P1 已完成，没有遗留待办

---

## 4. P2 进度

### 4.1 原始定位

P2 在当时的优先级清单里属于“更进一步的平台化/泛化治理能力”，优先级低于当前主链路稳态问题。

### 4.2 已完成项

- [ ] 无

### 4.3 未完成项

- [ ] 更通用的前置路由与意图治理
- [ ] 更系统的工具协议标准化
- [ ] 更完善的降级、熔断、重试、观测闭环

### 4.4 建议补充的具体功能

如果后续正式启动 P2，建议至少拆成下面这些可交付功能，而不是只停留在抽象治理层面：

- [ ] 扩展前置路由覆盖面
  - 将当前只覆盖“我的挂号 / 取消挂号 / 确认挂号”的前置路由，扩展到以下高频确定性意图：
    - 查询科室
    - 查询医生
    - 查询医生排班
    - 侧栏结构化动作直达业务链路
  - 目标是让“查科室 -> 查医生 -> 查排班 -> 确认挂号”这一整段高频路径，尽量少依赖模型自由决定工具顺序

- [ ] 增加统一意图匹配注册表
  - 把当前分散在前置路由中的关键词判断，收敛成可维护的意图规则表
  - 每条规则至少包含：
    - 意图名
    - 匹配条件
    - 命中后的处理函数
    - 未命中时是否继续走 LangGraph
  - 目标是降低继续加路由时的分支膨胀和 if/else 堆积

- [ ] 统一工具响应协议
  - 把所有工具的结果收敛到稳定协议，例如：
    - `ok`
    - `summary`
    - `data`
    - `hint`
    - `error_type`
  - 明确约束：
    - 成功时哪些字段必填
    - 失败时哪些字段必填
    - 空结果和异常结果如何区分
  - 目标是减少 orchestrator 和前端对“特殊字符串”做兼容判断

- [ ] 增加工具结果标准化与校验层
  - 在工具返回后增加统一的 normalize/validate 步骤
  - 处理以下常见问题：
    - 字段缺失
    - 字段类型不一致
    - `ok=true` 但没有可展示结果
    - 错误提示不适合直接给用户展示
  - 目标是把“工具协议兼容逻辑”从聊天编排层继续剥离出去

- [ ] 增加依赖异常的统一执行策略
  - 为 HMS、Redis、LLM 相关调用补上统一的：
    - 超时控制
    - 有限重试
    - 降级返回
    - 错误分类透传
  - 要求普通接口和 SSE 接口命中同一套策略，不再分别处理

- [ ] 增加最小可用观测闭环
  - 在现有日志基础上继续补齐：
    - 前置路由命中率
    - 各工具调用成功/失败统计
    - 降级响应触发统计
    - 常见错误类型分布
  - 目标是后续能回答“到底是模型没选对工具，还是 HMS 失败，还是工具协议不稳定”

### 4.5 当前可对照结论

- P2 没有开始实施
- 当前代码里没有形成这一层的独立闭环

---

## 5. P3 进度

### 5.1 原始定位

P3 在当时的优先级清单里属于“更长期、更重的架构升级项”，不是本轮稳态优先方案的一部分。

### 5.2 已完成项

- [ ] 无

### 5.3 未完成项

- [ ] 更大范围的编排层重构
- [ ] 更平台化的治理能力抽象
- [ ] 更彻底的状态机化或工作流化改造

### 5.4 建议补充的具体功能

如果后续正式启动 P3，建议把“长期架构升级”落成下面这些具体能力：

- [ ] 将挂号主链路显式状态机化
  - 把当前依赖轻量 `FlowState` 的挂号确认流程，升级为显式状态流转
  - 建议至少定义以下状态：
    - 待选科室
    - 待选医生
    - 待选日期/排班
    - 待确认挂号
    - 已创建挂号
    - 已取消挂号
  - 每个状态明确：
    - 允许的用户输入
    - 允许的工具调用
    - 缺失信息时的补问策略
    - 非法跳转时的拒绝策略

- [ ] 将开放式问答与强流程业务拆成双轨编排
  - 把“普通咨询/导诊问答”和“挂号、取消、确认等强流程操作”拆成两类执行路径
  - 强流程路径优先走规则或工作流节点
  - 开放式路径继续保留 LangGraph + tool calling
  - 目标是减少一个 agent 同时承担“自由问答”和“事务执行”导致的复杂性

- [ ] 引入工作流节点与执行器抽象
  - 为强流程动作定义标准节点接口，例如：
    - `load_context`
    - `resolve_entities`
    - `query_schedule`
    - `confirm_registration`
    - `create_registration`
    - `cancel_registration`
  - 节点之间通过明确的输入输出契约连接，而不是继续靠自然语言上下文串联

- [ ] 增加事务型操作的幂等与恢复机制
  - 对创建挂号、取消挂号这类有副作用操作补齐：
    - 幂等保护
    - 重复提交防护
    - 中断后恢复
    - 失败后明确状态回滚或重试指引
  - 目标是让后续接入更多事务型业务时不重复踩坑

- [ ] 抽象统一业务工作流框架
  - 在挂号主链路跑通后，把同一套 workflow 能力复用于未来的：
    - 缴费
    - 报告查询
    - 候诊进度
    - 院内导航
  - 这一步的重点不是立刻做完这些业务，而是先把“可复用的流程执行底座”搭出来

- [ ] 建立更清晰的编排边界
  - 明确区分以下层次：
    - API 层
    - Orchestrator 层
    - Workflow/State Machine 层
    - Tool Adapter 层
    - HMS Client 层
  - 目标是后续任何一个层次扩展时，都不需要再把逻辑堆回 `orchestrator.py` 或 `nodes.py`

### 5.5 当前可对照结论

- P3 没有开始实施
- 当前仍保持“在现有 LangGraph 主结构上做稳态增强”的路线

---

## 6. 本轮新增验证证据

- [x] 修复相关回归测试通过
  - 命令:
    - `../.venv-py312/bin/python -m pytest tests/test_guardrails/test_chat_output_filters.py tests/test_api/test_chat_orchestrator.py tests/test_tools/test_registration_flow_tools.py tests/test_api/test_chat_stream_api.py -q`
  - 结果:
    - `14 passed, 1 warning`

- [x] Docker 后端已重建并验证
  - 命令:
    - `docker compose up -d --build patient_agent_backend`

- [x] 真实联调验证通过
  - 已验证“帮我预约韩倩倩今天上午的号”能够返回正确排班结果
  - 已验证最终用户可见消息不再混入 `think:`、`查询医生排班`、`成功`、`ules。` 等噪声

---

## 7. 最终结论

如果以后继续按这份“改造优先级清单”推进，可以直接按下面结论对照:

- `P0`: 已完成
- `P1`: 已完成
- `P2`: 未开始
- `P3`: 未开始

如果后续需要继续推进，建议下一步从 `P2` 开始单独拆分为新的设计文档和实施计划，而不是继续把它们混在本轮 `P0/P1` 文档里。
