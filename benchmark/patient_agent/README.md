# patient_agent Benchmark

## 目标

这套 benchmark 用于给 `patient_agent_backend` 与 `patient_agent_frontend` 提供一份可持续复用的回归测试基线，服务于后续功能修复、需求开发、接口重构和前后端联调。

它只覆盖两类能力：

- PRD 中已要求，且当前代码中已经具备明确实现或已有稳定交互闭环的能力
- 当前仓库里已经存在代码依据、测试依据或前后端联动依据的能力

它不会覆盖以下两类能力：

- PRD 中规划了但当前仓库尚未落地的能力
- 当前仅有概念描述、没有稳定输入输出边界的能力

## 目录结构

- `feature-matrix.md`
  - PRD 功能点与当前实现状态的对照表
  - 明确哪些能力被纳入 benchmark，哪些暂不纳入
- `patient-agent-benchmark.json`
  - 机器可读 benchmark 数据
  - 后续可直接被 `pytest`、`vitest`、Playwright 或自定义回归脚本消费
- `frontend-e2e-cases.md`
  - 前端页面旅程型 e2e 回归清单
  - 适合人工回归、产品验收和页面级联调走查
- `patient-agent-frontend-e2e.json`
  - 前端页面旅程型 e2e 机器可读数据
  - 用于后续 Playwright、Vitest 页面级集成测试或自定义回归脚本

## 当前纳入范围

- 认证
  - 发送短信验证码
  - 验证码登录
  - 登出鉴权
- 聊天与线程
  - 普通聊天
  - SSE 流式聊天
  - 历史会话读取
  - 会话列表读取
  - 删除会话
  - 患者会话隔离
- 患者档案与侧栏
  - 获取患者档案
  - 更新患者档案字段约束
  - 右侧栏动作透传到对话流
  - 本地缓存恢复与线程上下文续聊
- 就医流程能力
  - 科室/医生/排班相关挂号流转
  - 待确认挂号状态写入
  - 确认挂号
  - 查询挂号记录
  - 取消挂号引导
- 安全护栏
  - 诊断请求拦截
  - 报告解读拦截
  - 高危应急识别
  - 健康话题免责声明
  - 输出免责声明追加去重

## 当前不纳入范围

以下功能虽然出现在 PRD 中，但当前代码里未形成稳定闭环，或仍处于规划/部分实现状态，因此不纳入这版 benchmark：

- 院内导航
- 候诊进度
- 报告查询结果展示与 PDF 下载
- 缴费引导
- 用药提醒
- 复诊提醒
- 满意度评价
- 运营后台与知识库管理
- 严格规则化的“症状分诊引擎”
- 严格规则化的“医生推荐引擎”

## 使用方式

### 1. 作为人工回归清单

按 `patient-agent-benchmark.json` 的 case 顺序逐条验证：

- 先准备患者登录态
- 再按模块执行接口或页面动作
- 对比 `expected` 与 `forbidden` 字段

### 2. 作为自动化数据源

建议把 JSON 中的 case 分成三层：

- API 层
  - 直接驱动 FastAPI 接口测试
- 前端层
  - 驱动 `vitest` 组件测试或页面状态测试
- 集成层
  - 驱动登录 -> 聊天 -> 线程恢复 -> 挂号确认的端到端回归

### 3. 作为需求变更基线

后续新增功能时，建议同时更新：

- `feature-matrix.md` 中的“当前实现状态”
- `patient-agent-benchmark.json` 中新增模块和 case

### 4. 作为前端页面回归入口

建议按页面旅程顺序执行：

- 先跑登录旅程，确认未登录到聊天页入口稳定
- 再跑历史线程恢复和当前线程续聊旅程
- 然后跑右侧栏 fallback、挂号确认和新线程续聊旅程
- 最后跑线程删除成功/失败两个分支

### 5. 作为真实页面级 E2E 回归入口

宿主机执行 Playwright，前后端运行在本机 Docker 中：

    bash scripts/patient-agent-e2e.sh

如需只跑单个 spec：

    bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/thread-delete.spec.js

## 数据设计约定

每条 case 至少包含以下字段：

- `id`
- `module`
- `scenario`
- `prd_features`
- `preconditions`
- `input`
- `expected`
- `forbidden`
- `evidence`

其中：

- `expected` 表示本轮回归必须成立的断言
- `forbidden` 表示即使功能“看起来可用”，也不允许出现的行为
- `evidence` 只引用当前仓库里的代码或测试文件，避免 benchmark 与实现脱节

## 推荐执行顺序

建议按以下顺序跑回归：

1. `auth`
2. `chat_core`
3. `chat_stream`
4. `thread_cache`
5. `patient_profile_sidebar`
6. `registration_flow`
7. `guardrails`

## 维护建议

- 当后端新增稳定接口时，优先补 `patient-agent-benchmark.json`
- 当前端新增稳定交互时，同步补充 `feature-matrix.md`
- 当 PRD 功能从“规划”变成“已实现”时，再把它从“不纳入范围”迁移到正式 benchmark
