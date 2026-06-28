# patient_agent 功能覆盖矩阵

## 说明

- `已纳入`：PRD 中要求且当前代码已有明确实现闭环，已进入 benchmark
- `部分实现`：代码中有入口或局部能力，但还不适合作为稳定 benchmark 基线
- `未实现`：PRD 有要求，但当前仓库未形成可验证闭环

## 功能矩阵

| PRD 一级功能 | PRD 二级功能 | 当前状态 | Benchmark Case ID | 代码/测试依据 |
|---|---|---|---|---|
| 智能就医引导 | 症状->科室匹配 | 部分实现 | - | `patient_agent_backend/app/agent/prompts.py`、`patient_agent_backend/app/guardrails/input_guard.py` |
| 智能就医引导 | 科室介绍/科室查询 | 已纳入 | `REG-001` | `patient_agent_backend/app/tools/dept_tools.py`、`patient_agent_frontend/src/App.jsx` |
| 智能就医引导 | 就诊流程引导 | 已纳入 | `CHAT-001`、`CHAT-002`、`REG-004` | `patient_agent_backend/app/api/chat.py`、`patient_agent_backend/app/chat/pre_router.py` |
| 智能就医引导 | 院内导航 | 未实现 | - | PRD 存在，当前前后端无稳定导航闭环 |
| 医生资源查询 | 医生信息查询 | 已纳入 | `REG-001`、`REG-004` | `patient_agent_backend/app/tools/doctor_tools.py`、`patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx` |
| 医生资源查询 | 实时排班查询 | 已纳入 | `REG-001`、`REG-004` | `patient_agent_backend/tests/test_tools/test_registration_flow_tools.py`、`patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx` |
| 医生资源查询 | 医生推荐 | 部分实现 | - | PRD 有规则匹配要求，当前仓库无稳定推荐引擎闭环 |
| 就诊事务办理 | 智能挂号/预约 | 已纳入 | `REG-001`、`REG-002`、`REG-003`、`REG-006`、`REG-007` | `patient_agent_backend/tests/test_integration/test_chat_registration_flow.py`、`patient_agent_backend/tests/test_tools/test_registration_flow_state.py` |
| 就诊事务办理 | 候诊进度查询 | 未实现 | - | PRD 有要求，当前仓库无稳定叫号/等待时间闭环 |
| 就诊事务办理 | 报告查询 | 部分实现 | `GUARD-002` | 当前主要是“拒绝解读报告”，未实现报告状态/查看/下载闭环 |
| 就诊事务办理 | 缴费引导 | 未实现 | - | PRD 有要求，当前仓库无支付/待缴费清单闭环 |
| 诊后服务管理 | 用药提醒 | 未实现 | - | PRD 有要求，当前仓库无提醒调度闭环 |
| 诊后服务管理 | 复诊提醒 | 未实现 | - | PRD 有要求，当前仓库无提醒调度闭环 |
| 诊后服务管理 | 满意度评价 | 未实现 | - | PRD 有要求，当前仓库无评价问卷闭环 |
| 安全护栏 | 诊断请求拦截 | 已纳入 | `GUARD-001` | `patient_agent_backend/tests/test_guardrails/test_input_guard.py` |
| 安全护栏 | 报告解读拦截 | 已纳入 | `GUARD-002` | `patient_agent_backend/app/guardrails/input_guard.py` |
| 安全护栏 | 高危应急识别 | 已纳入 | `GUARD-003` | `patient_agent_backend/app/guardrails/input_guard.py` |
| 安全护栏 | 健康话题免责声明 | 已纳入 | `GUARD-004`、`GUARD-005` | `patient_agent_backend/tests/test_guardrails/test_output_guard.py` |
| 认证与身份 | 验证码发送 | 已纳入 | `AUTH-001` | `patient_agent_backend/app/api/auth.py` |
| 认证与身份 | 验证码登录 | 已纳入 | `AUTH-002`、`AUTH-003` | `patient_agent_backend/tests/test_api/test_auth_api.py` |
| 认证与身份 | 登出鉴权 | 已纳入 | `AUTH-004` | `patient_agent_backend/tests/test_api/test_auth_api.py` |
| 对话会话 | 普通聊天 | 已纳入 | `CHAT-001`、`CHAT-002` | `patient_agent_backend/tests/test_api/test_chat_auth.py` |
| 对话会话 | SSE 流式聊天 | 已纳入 | `STREAM-001`、`STREAM-002` | `patient_agent_backend/tests/test_api/test_chat_stream_api.py` |
| 对话会话 | 历史会话查询 | 已纳入 | `CHAT-003`、`CHAT-004`、`THREAD-001`、`THREAD-002` | `patient_agent_backend/tests/test_api/test_chat_threads_api.py`、`patient_agent_frontend/src/storage/patientHistoryRecovery.test.js` |
| 对话会话 | 会话删除 | 已纳入 | `CHAT-005`、`THREAD-004` | `patient_agent_backend/tests/test_api/test_chat_threads_api.py`、`patient_agent_frontend/src/App.delete-thread.test.jsx` |
| 患者工作台 | 档案查询 | 已纳入 | `PROFILE-001` | `patient_agent_backend/tests/test_api/test_patient_profile_api.py` |
| 患者工作台 | 档案更新字段约束 | 已纳入 | `PROFILE-002` | `patient_agent_backend/tests/test_api/test_patient_profile_api.py` |
| 患者工作台 | 侧栏动作续接对话 | 已纳入 | `SIDEBAR-001`、`THREAD-003` | `patient_agent_backend/tests/test_api/test_sidebar_action_api.py`、`patient_agent_frontend/src/App.thread-context.test.jsx` |

## 当前可作为主回归入口的能力

- 登录并拿到真实 `patient_id`
- 发送普通聊天消息并强制使用登录患者身份
- 发送 SSE 流式消息并校验事件边界
- 读取历史线程并恢复到患者本地缓存
- 删除线程时校验本地/远端状态处理
- 从右侧栏进入挂号确认并续接当前 thread
- 通过挂号待确认状态完成“查询排班 -> 选择时段 -> 确认挂号”
- 拦截诊断类、高危类、报告解读类输入

## 暂不建议纳入严格自动化基线的能力

- 仅依赖大模型自由生成、但没有稳定工具输出约束的“导诊建议”
- 仅在 PRD 中定义、尚未在前后端形成稳定数据模型的功能
- 需要外部系统完整对接但仓库里没有稳定 fixture 的功能
