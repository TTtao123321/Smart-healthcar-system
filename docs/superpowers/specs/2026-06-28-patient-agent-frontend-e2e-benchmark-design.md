# patient_agent 前端页面操作流 Benchmark 设计

## 背景

当前仓库已经具备一版面向能力基线的 `patient_agent` benchmark，覆盖认证、聊天、线程、患者档案、挂号流程与安全护栏。但它主要站在“接口/能力”视角，尚未单独沉淀一版面向前端真实页面旅程的 e2e benchmark。

这会带来两个问题：

- 后续修复前端页面状态、线程续聊、侧栏挂号交互时，缺少统一的页面级回归清单
- 后续接入 Playwright 或其他 e2e 框架时，需要重新从页面行为角度拆 case

因此，需要在现有 `benchmark/patient_agent` 下新增一版前端页面操作流 benchmark。

## 目标

新增一套可复用的前端 e2e benchmark，满足以下目标：

- 用真实患者旅程组织回归场景，而不是单纯罗列接口
- 既适合人工回归，也适合后续自动化脚本直接消费
- 与现有能力基线 benchmark 保持字段风格一致
- 只覆盖当前前端页面已经形成稳定交互闭环的能力

## 非目标

本次不做以下工作：

- 不直接生成 Playwright 可执行代码
- 不扩展未落地的页面功能
- 不把后端 API benchmark 机械复制为前端页面 benchmark
- 不为当前前端不存在的页面强行设计 case

## 当前前端页面闭环

根据 `patient_agent_frontend` 当前实现，已形成稳定页面闭环的主路径如下：

1. 登录页
   - 输入手机号
   - 获取验证码
   - 输入验证码
   - 登录成功后进入聊天页
2. 聊天页
   - 恢复线程列表
   - 恢复当前 thread
   - 发送消息
   - 消费 SSE 响应
3. 右侧栏
   - 加载患者侧栏数据
   - 展示患者档案与排班
   - 选择医生并触发挂号确认
   - 侧栏动作续接当前聊天线程
4. 线程管理
   - 历史线程切换
   - 页面重载后续聊
   - 删除线程
   - 删除失败回滚

## 设计原则

### 1. 主视角按患者旅程组织

case 应按真实患者使用顺序组织，例如：

- 登录成功进入聊天页
- 恢复历史线程
- 在当前 thread 继续发送消息
- 从右侧栏确认挂号
- 使用新的 thread 继续对话
- 删除线程并处理失败分支

### 2. 子视角保留页面区域定位

每条 case 除了旅程标识外，还要标记页面区域，便于后续定位问题：

- `login_page`
- `chat_page.left_panel`
- `chat_page.center_panel`
- `chat_page.right_sidebar`
- `thread_management`

### 3. 与现有 benchmark 风格保持一致

新增前端 e2e benchmark 的数据结构需要与现有 `patient-agent-benchmark.json` 保持同类语义，避免后续维护出现两套风格。

### 4. 明确“页面断言”与“禁止行为”

每条 case 必须同时包含：

- 期望页面行为
- 不允许出现的错误行为

例如：

- 期望：页面刷新后仍在原 thread 中发送消息
- 禁止：刷新后悄悄创建新 thread

## 交付物

本次新增两个文件：

### 1. `benchmark/patient_agent/frontend-e2e-cases.md`

用途：

- 给人工回归使用
- 给测试评审和产品验收使用

内容要求：

- 按旅程分组
- 每条 case 明确页面入口、前置条件、操作步骤、断言、失败信号
- 与现有 benchmark case 做关联

### 2. `benchmark/patient_agent/patient-agent-frontend-e2e.json`

用途：

- 给后续 Playwright、Vitest 页面级集成测试或自定义回归脚本消费

字段要求：

- `benchmark_id`
- `generated_on`
- `based_on`
- `journeys`
- `cases`

每条 case 至少包含：

- `id`
- `journey`
- `page`
- `priority`
- `related_case_ids`
- `preconditions`
- `steps`
- `expected`
- `forbidden`
- `evidence`

## 旅程清单

本次计划覆盖以下 10 类前端页面旅程：

1. 登录成功进入聊天页
2. 登录页输入校验失败
3. 进入聊天页后恢复历史线程
4. 在当前线程发送消息并消费 SSE
5. 页面刷新后继续在原线程续聊
6. 右侧栏加载失败时使用 fallback 展示
7. 右侧栏选择医生并确认挂号
8. 侧栏动作返回新 thread 后继续在该 thread 聊天
9. 删除线程成功
10. 删除线程失败时保留本地缓存并提示错误

## 旅程拆分规则

### 登录相关

覆盖登录页最小可执行闭环：

- 手机号合法性校验
- 验证码必填校验
- 获取验证码后进入倒计时
- 登录成功后写入当前 session 并进入聊天页

### 聊天页相关

覆盖聊天页最小主链路：

- 初始恢复历史线程
- 当前 thread 的消息展示
- 发送消息时使用当前 thread_id
- SSE 返回后更新消息区

### 右侧栏相关

覆盖右侧栏最小主链路：

- 侧栏加载成功
- 侧栏加载失败 fallback
- 选择科室/医生
- 弹出确认挂号
- 触发侧栏动作

### 线程相关

覆盖线程管理的稳定断言：

- 页面重载后续聊
- 侧栏动作切换 server thread
- 删除线程成功
- 删除线程失败时 UI 与缓存回滚

## 证据来源

本次前端 e2e benchmark 只允许引用当前仓库中已存在的实现或测试作为证据来源，主要包括：

- `patient_agent_frontend/src/App.jsx`
- `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`
- `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`
- `patient_agent_frontend/src/App.thread-context.test.jsx`
- `patient_agent_frontend/src/App.delete-thread.test.jsx`
- `patient_agent_frontend/src/storage/patientHistoryRecovery.test.js`
- 已生成的 `benchmark/patient_agent/patient-agent-benchmark.json`

## 不纳入本次前端 e2e 范围的页面能力

以下内容暂不纳入前端 e2e benchmark：

- 报告详情页或 PDF 下载页
- 候诊进度实时刷新页
- 缴费页或支付跳转页
- 用药提醒配置页
- 满意度评价页
- 院内导航地图页

原因是当前前端仓库中还没有稳定、独立、可执行的页面闭环。

## 验收标准

完成后应满足：

1. `benchmark/patient_agent` 下新增一份 Markdown e2e case 清单
2. `benchmark/patient_agent` 下新增一份机器可读 JSON
3. 所有 case 都能映射到当前前端页面行为
4. 所有 case 都至少有一个仓库内证据引用
5. JSON 可被标准解析器直接读取

## 实现后维护约定

- 若新增前端稳定页面流，优先补 `patient-agent-frontend-e2e.json`
- 若页面流程变更导致旅程变化，同步更新 `frontend-e2e-cases.md`
- 若某条旅程对应的能力基线 case 已更新，需回查 `related_case_ids`
