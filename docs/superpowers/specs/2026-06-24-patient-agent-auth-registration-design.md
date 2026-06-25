# patient_agent 患者认证与挂号链路打通设计

**日期：** 2026-06-24
**范围：** `patient_agent_backend`、`patient_agent_frontend`、`hospital_manage_backend`

## 概述

本次改造目标是统一患者身份来源，移除 HMS 侧独立患者登录链路，由 `patient_agent_backend` 作为唯一患者认证入口，直接对接 HMS 患者主数据表 `patient_user_info`，并打通“登录 -> 患者档案 -> Agent 上下文 -> 挂号”的完整链路。

改造完成后：

- 患者登录只走 `patient_agent_backend /api/auth/*`
- 患者真实身份统一为 `patient_user_info.id`
- 聊天、SSE、对话历史、挂号工具统一从 token 解析患者身份
- `patient_agent_frontend` 不再依赖前端透传的伪 `patient_id`
- HMS 删除患者侧认证实现，仅保留管理端认证和业务接口

## 当前问题

### 1. 患者身份未对齐

- `patient_agent_backend` 当前登录成功后固定返回 `patient_id=0`
- 聊天接口和工具链主要依赖前端请求体中的 `patient_id`
- 挂号工具实际需要的是 HMS 患者卡号/患者主键，但当前没有与 `patient_user_info.id` 建立真实绑定

### 2. 认证链路重复

- HMS 后端存在一套患者短信验证码登录服务
- `patient_agent_backend` 又自建了一套短信验证码登录
- 两套逻辑并行存在，但 token、患者 ID、会话上下文并不互通

### 3. 挂号链路未完全闭环

- 查询挂号和取消挂号可以落到当前 HMS 已有接口
- 创建挂号依赖 `POST /medical_registration/save`
- 当前仓库中未检索到该接口的 Java Controller/Service/Mapper 实现，说明创建挂号后端落点缺失或与当前代码分支不一致

## 设计目标

### 业务目标

- 让患者在 Agent 端登录后获得真实的 HMS 患者身份
- 让患者档案信息与 `patient_user_info` 保持一致
- 让 Agent 端挂号自动使用当前登录患者身份，不允许伪造患者 ID

### 技术目标

- 认证入口单一化
- 患者身份全链路统一
- 患者档案读写边界清晰
- 对现有前端交互影响最小
- 为后续患者档案编辑、病历查询、处方查询预留统一身份基础

## 推荐方案

采用“Agent 唯一认证入口 + 直接对接患者主表 + HMS 仅保留业务接口”的方案。

### 方案说明

- `patient_agent_backend` 负责短信验证码发送、验证码校验、token 签发、登录态存储
- `patient_agent_backend` 直接访问 HMS MySQL，读写 `patient_user_info`
- 登录成功后，返回真实 `patient_user_info.id` 作为 `patient_id`
- 聊天与工具调用从 token 中恢复患者身份，并注入请求上下文
- HMS 删除患者端认证服务与相关控制器/暴露入口
- 创建挂号接口由 HMS 后端补齐 `POST /medical_registration/save`，供 Agent 继续复用

### 不采用的方案

- 不采用“保留 HMS 患者认证接口，Agent 转发调用”的方案，因为认证归属与本次约束冲突
- 不采用“继续前端透传 patient_id”的方案，因为存在伪造患者身份风险

## 整体架构

```text
patient_agent_frontend
    -> /api/auth/send-sms
    -> /api/auth/login
    -> 保存 token 与真实 patient_id
    -> /api/chat | /api/chat/stream | /api/chat/history

patient_agent_backend
    -> Redis: 短信验证码、登录态 token
    -> MySQL: patient_user_info
    -> HMS HTTP API: 科室、医生、排班、挂号、取消挂号、查询挂号

hospital_manage_backend
    -> 保留管理端登录 /user/login
    -> 保留患者、挂号、医生、科室业务接口
    -> 删除患者短信认证链路
    -> 补齐 /medical_registration/save
```

## 模块设计

### 1. patient_agent_backend 认证模块

保留现有 `/api/auth/send-sms` 与 `/api/auth/login` 路由，但重构其实现。

#### `/api/auth/send-sms`

- 继续使用 Redis 保存验证码
- 保持现有开发模式行为，可返回 `code_dev`
- 不依赖 HMS 患者认证服务

#### `/api/auth/login`

登录流程调整为：

1. 校验 Redis 验证码
2. 按手机号查询 `patient_user_info.tel`
3. 若不存在，则自动创建患者档案
4. 生成 Agent 自有 token
5. Redis 保存 `token -> patient_id / phone / name / login_time`
6. 返回真实 `patient_id`

返回结构保持兼容：

```json
{
  "token": "string",
  "patient_id": 123,
  "name": "张三"
}
```

#### `/api/auth/logout`

- 从 Redis 删除当前 token 对应登录态
- 前提是该接口能从请求头拿到 Bearer token

### 2. patient_user_info 对接层

`patient_agent_backend` 新增数据库访问层，直接对接 HMS 库中的 `patient_user_info`。

建议新增结构：

```text
app/patient_profile/
├── models.py
├── repository.py
└── service.py
```

#### Repository 职责

- `get_by_phone(phone)`
- `get_by_id(patient_id)`
- `create_patient(profile)`
- `update_patient_basic_info(patient_id, payload)`

#### 首期对接字段

- `id`
- `uuid`
- `name`
- `sex`
- `pid`
- `tel`
- `birthday`
- `insurance_type`
- `medical_history`
- `allergy_history`
- `family_history`

#### 自动建档规则

- 手机号首次登录时自动创建患者
- 默认姓名沿用当前逻辑：`患者{手机号后四位}`，后续允许档案补全
- `uuid` 自动生成
- 其余非必填字段默认留空

### 3. 登录态与鉴权上下文

当前系统虽然在前端附加了 `Authorization`，但后端聊天接口并未真正校验 token。本次需要补齐认证依赖。

建议新增结构：

```text
app/auth/
├── dependencies.py
├── models.py
└── service.py
```

#### 鉴权规则

- 所有患者侧接口从 `Authorization: Bearer <token>` 解析登录态
- `chat`、`chat/stream`、`chat/history` 必须要求已登录
- `logout` 必须要求已登录
- `send-sms`、`login` 保持匿名可访问

#### 上下文注入

- 请求认证成功后，将真实 `patient_id` 注入请求上下文
- `request_context.py` 不再信任前端请求体中的 `patient_id`
- 会话记忆键从“前端透传 patient_id”改为“token 解析得到的真实 patient_id”

### 4. 患者档案接口

为前端补充患者档案信息对接，建议新增以下接口：

#### `GET /api/patient/profile`

- 返回当前登录患者档案
- 数据来源：`patient_user_info`

返回字段：

```json
{
  "id": 123,
  "name": "张三",
  "sex": "男",
  "pid": "110101199001011234",
  "tel": "13800000000",
  "birthday": "1990-01-01",
  "insurance_type": "医保",
  "medical_history": "",
  "allergy_history": "",
  "family_history": ""
}
```

#### `POST /api/patient/profile`

- 更新当前登录患者的基础档案
- 仅允许更新基础字段，不允许前端改 `id`、`uuid`、`tel`

首期可编辑字段：

- `name`
- `sex`
- `pid`
- `birthday`
- `insurance_type`
- `medical_history`
- `allergy_history`
- `family_history`

### 5. 聊天与工具链改造

#### 聊天接口

- `POST /api/chat`
- `POST /api/chat/stream`
- `GET /api/chat/history`

改造要点：

- 不再要求前端传入 `patient_id`
- 若前端仍传入，后端忽略该字段
- 后端从 token 解析真实 `patient_id`
- 所有记忆、线程隔离、工具调用都使用真实患者 ID

#### 工具链

`registration_tools.py` 保持“显式参数优先、上下文兜底”的接口形式，但默认上下文必须来自认证态。

核心变化：

- `get_patient_id()` 只返回登录上下文中的真实患者 ID
- 若无认证上下文，则挂号类工具直接报错“请先登录”
- `create_registration` 默认使用当前登录患者的 `patient_user_info.id`

### 6. HMS 后端改造

#### 删除患者认证链路

从 `hospital_manage_backend` 中移除：

- `PatientPortalAuthService`
- `PatientPortalAuthServiceImpl`
- 患者端独立 `StpPatientUtil` / `StpPatientConfig` 及相关患者登录暴露入口

注意：

- 只删除患者认证相关代码
- 不影响管理端 `UserController`、`StpUtil`、后台权限体系

#### 保留的 HMS 能力

- `/user/login` 供管理端使用
- `/patient/selectByPage`
- `/patient/selectDetail`
- `/patient/updateRegistrationStatus`
- 科室、医生、排班相关查询接口

#### 新增或补齐的 HMS 能力

- `POST /medical_registration/save`

该接口至少需要支持以下字段：

- `patientCardId`
- `doctorId`
- `deptSubId`
- `date`
- `slot`

并满足以下约束：

- 校验患者是否存在
- 校验医生排班是否存在
- 校验剩余号源是否足够
- 成功后写入 `medical_registration`

### 7. 前端改造

#### 登录页

- 登录交互保持不变，仍为“手机号 + 验证码”
- 登录成功后保存真实 `patient_id`

#### 聊天请求

- 继续自动附带 Bearer token
- 发送聊天时不再传 `patient_id`
- 对话线程仍由前端本地维护 `thread_id`

#### 患者档案页

若当前前端暂无档案页，首期可只做接口对接，不强制新增页面。

若补充页面，建议最小能力为：

- 查看档案
- 完善姓名、性别、身份证、生日、保险类型
- 完善既往史、过敏史、家族史

## 数据流

### 登录链路

```text
手机号 + 验证码
-> patient_agent_backend 校验验证码
-> 查询 patient_user_info
-> 不存在则自动建档
-> 生成 token
-> Redis 保存登录态
-> 前端保存 token + patient_id
```

### 对话链路

```text
前端发送 Bearer token + message + thread_id
-> 后端解析 token
-> 注入真实 patient_id 到上下文
-> Agent 执行工具
-> 工具默认读取真实 patient_id
-> 返回结果
```

### 挂号链路

```text
患者发起挂号
-> Agent 选择 create_registration
-> 工具从认证上下文读取 patient_id
-> HMS /medical_registration/save
-> 写入 medical_registration
-> 返回挂号结果
```

## 错误处理

### 认证错误

- token 缺失：返回 401
- token 无效或过期：返回 401
- 验证码错误：返回 400
- 验证码过期：返回 400

### 患者档案错误

- 患者不存在：返回 404
- 档案更新参数非法：返回 400
- 手机号重复或数据异常：返回 409 或 500

### 挂号错误

- 未登录：返回“请先登录后再挂号”
- 未提供足够挂号信息：工具提示继续补充
- HMS 无排班或无号源：返回明确业务提示
- HMS 创建挂号接口不存在：在开发阶段视为高优先级阻断问题

## 安全要求

- 后端不信任前端传入的 `patient_id`
- 患者 token 仅用于患者侧接口，不与 HMS 管理端 token 混用
- Redis 登录态设置有效期，并支持登出失效
- 患者档案更新接口仅允许修改当前登录患者自身档案
- 日志中避免输出完整身份证号、手机号验证码、完整 token

## 测试策略

### 后端

- 认证接口测试
  - 发送验证码
  - 正确验证码登录
  - 错误验证码登录失败
  - 首次登录自动建档
- 患者档案接口测试
  - 查询当前患者档案
  - 更新档案成功
  - 未登录访问失败
- 聊天鉴权测试
  - 无 token 访问失败
  - 有 token 时真实 patient_id 注入成功
- 挂号工具测试
  - 使用真实 patient_id 创建挂号
  - 无认证上下文时拒绝挂号

### 前端

- 登录成功后本地保存真实 `patient_id`
- token 过期时自动清理本地登录态
- 聊天请求不再依赖手工传入患者 ID

## 实施顺序

1. 为 `patient_agent_backend` 增加 `patient_user_info` 数据访问层
2. 重构 `/api/auth/login`，返回真实患者 ID
3. 新增患者鉴权依赖，接入 `chat`、`chat/stream`、`chat/history`、`logout`
4. 新增患者档案查询/更新接口
5. 改造前端请求，去除对透传 `patient_id` 的依赖
6. 改造挂号工具，统一从认证上下文读取患者身份
7. 删除 HMS 患者认证链路代码
8. 补齐 HMS `POST /medical_registration/save`
9. 联调“登录 -> 查看档案 -> 发起挂号 -> 查询挂号 -> 取消挂号”全流程

## 兼容性说明

- `patient_agent_frontend` 登录交互保持不变
- 旧版仍传 `patient_id` 的聊天请求在首期可兼容接收，但后端会忽略该字段
- 若 `medical_registration/save` 暂未补齐，则本次只能先完成“认证 + 档案 + 查询/取消挂号”，创建挂号不能宣称完成

## 验收标准

- 患者登录后返回的 `patient_id` 等于 `patient_user_info.id`
- 患者首次登录时能自动创建 `patient_user_info` 记录
- 聊天接口在无 token 时拒绝访问
- 挂号工具默认使用当前登录患者身份，不接受伪造患者 ID
- 患者档案可查询并更新
- HMS 患者认证代码已删除，管理端认证不受影响
- 创建挂号接口可以在当前仓库真实落地并完成联调
