# 患者身份统一与挂号链路 patient_id 收敛设计

## 1. 背景

当前系统中，患者侧登录会话、聊天上下文和患者档案主要使用 `patient_id`，其值来自 `patient_user_info.id`。但挂号链路仍沿用 `patient_card_id` 命名，导致以下问题：

- 患者身份模型混乱，`patient_id` 和 `patient_card_id` 在当前实现中实际都指向 `patient_user_info.id`
- Python Agent 工具层仍允许显式传入 `patient_card_id`，存在“前端或 LLM 自由指定患者身份”的风险
- 挂号查询与取消的身份边界不够清晰，不利于实现严格的“本人数据隔离”

经确认，当前仓库中不存在独立的患者就诊卡表。挂号相关的 `patient_card_id` 实际指向 `patient_user_info.id`，因此本次采用一次性直接切换方案：删除挂号语义中的 `patient_card_id`，统一收敛为 `patient_id`。

## 2. 目标

本次改造的目标如下：

1. 将系统中的唯一合法患者身份统一为 `patient_user_info.id`
2. 删除挂号链路中的 `patient_card_id` 字段和相关业务命名
3. 将 `medical_registration` 及其所有上下游依赖统一改为 `patient_id`
4. 保证前端、请求体、LLM 工具均不能自由传入患者身份
5. 保证聊天、聊天历史、挂号查询、挂号创建、挂号取消均按当前登录患者隔离

## 3. 非目标

本次改造明确不包含以下内容：

- 不引入“常用就诊人”或“代家属挂号”能力
- 不保留 `patient_card_id` 兼容层
- 不把 `patient_user_info.uuid` 升级为新的独立就诊卡主标识
- 不对现有患者档案结构做超出本次身份收口范围的扩展

## 4. 统一身份模型

### 4.1 唯一身份源

- `patient_id` 为系统唯一合法患者身份标识
- `patient_id` 直接对应 `patient_user_info.id`
- 登录成功后，服务端 session 仅保存当前患者的 `patient_id`

### 4.2 废弃身份命名

以下业务命名视为彻底废弃：

- `patient_card_id`
- `patientCardId`
- 所有以“患者就诊卡 ID”为语义的挂号字段、请求参数、返回字段和测试数据

### 4.3 当前数据库语义

当前系统中：

- `patient_user_info.id` 是患者主键
- `medical_registration.patient_card_id` 实际上引用的是 `patient_user_info.id`
- 因此本次是“语义纠偏 + 全链路重命名”，不是引入新映射关系

## 5. 数据库改造

### 5.1 表结构调整

将 `medical_registration` 表中的字段：

- `patient_card_id` 重命名为 `patient_id`

调整后的语义为：

- `medical_registration.patient_id -> patient_user_info.id`

### 5.2 脚本更新范围

需要同步更新以下 SQL 资产：

- `hospital_manage_backend/init-sql/01-init.sql`
- `hospital_manage_backend/init-sql/04-init-patient-data.sql`
- `hospital_manage_backend/init-sql/05-init-schedule-test-data.sql`
- `hospital_manage_backend/hospital_hms_api/src/main/resources/schema.sql`

### 5.3 关联查询统一规则

所有挂号相关查询统一采用以下关联语义：

```sql
medical_registration.patient_id = patient_user_info.id
```

后续任何患者信息回查、近期就诊记录查询、详情聚合查询都不得再使用 `patient_card_id` 命名。

## 6. HMS Java 后端改造

### 6.1 涉及模块

需要修改以下挂号相关模块中的字段与命名：

- `MedicalRegistration`
- `InsertMedicalRegistrationForm`
- `MedicalRegistrationDao`
- `MedicalRegistrationDao.xml`
- `MedicalRegistrationService`
- `MedicalRegistrationServiceImpl`
- `MedicalRegistrationController`

需要同步修改以下患者查询相关模块中对挂号表的引用：

- `PatientDao`
- `PatientDao.xml`
- 依赖挂号表患者字段的 service / controller / test

### 6.2 字段统一规则

以下字段统一改名：

- Java 字段：`patientCardId -> patientId`
- JSON 请求字段：`patientCardId -> patientId`
- SQL 字段：`patient_card_id -> patient_id`
- 查询结果字段别名：`patientCardId -> patientId`

### 6.3 取消挂号权限规则

HMS Java 后端如存在“仅凭挂号 ID 即可直接取消”的路径，需要改为支持按患者归属校验。至少保证患者侧链路在调用取消前，能够验证目标挂号记录属于当前登录患者。

若当前 HMS controller 不直接承接患者登录态，则由 Python Agent 后端在调用 HMS 取消接口前先完成归属校验。

## 7. patient_agent_backend 改造

### 7.1 登录态与会话

- `PatientSession` 继续仅保存 `patient_id`
- 不新增 `patient_card_id`
- 所有业务上下文统一从 session 获取真实患者身份

### 7.2 聊天接口

以下接口继续强制依赖登录态：

- `/api/chat`
- `/api/chat/stream`
- `/api/chat/history`
- `/api/patient/profile`
- `/api/patient/sidebar`
- `/api/patient/profile` 更新接口

其中聊天与历史接口需要满足：

- 无论前端是否传入 `patient_id`，服务端都忽略
- 服务端仅使用 `session.patient_id`
- Redis 对话 key 继续使用 `patient_id + thread_id`

### 7.3 HMS Client 模型

Python 侧挂号模型统一改名：

- `RegistrationCreateRequest.patient_card_id -> patient_id`
- `RegistrationQueryRequest.patient_card_id -> patient_id`
- `RegistrationItem.patient_card_id -> patient_id`

对应的 HMS 请求 payload 与响应字段解析同步改为：

- `patientId`

### 7.4 挂号工具

`registration_tools.py` 需要执行以下约束：

- 删除 `create_registration` 中的 `patient_card_id` 入参
- 删除 `query_registration` 中的 `patient_card_id` 入参
- 工具只能通过当前请求上下文中的 `session.patient_id` 获取患者身份
- 工具描述中不再出现“可选传入患者就诊卡 ID”的说明

### 7.5 查询与取消归属规则

#### 查询挂号

- 查询本人挂号时，仅允许使用当前登录患者的 `patient_id`
- 若指定 `registration_id`，也必须校验该记录归属当前患者

#### 取消挂号

- 不允许仅凭 `registration_id` 直接取消
- 必须先校验该挂号记录属于当前登录患者
- 若记录不存在或不属于当前患者，返回“记录不存在或无权限”

### 7.6 侧栏聚合

`patient_sidebar` 中查询近期记录的参数和内部命名全部统一改为 `patient_id`，不得继续使用 `patient_card_id` 语义。

## 8. patient_agent_frontend 改造

### 8.1 前端身份边界

前端保留以下本地状态：

- `token`
- `patient_id`

但这些状态仅用于：

- 发起登录后已鉴权请求
- 本地展示

前端不得在聊天、挂号、患者档案请求体中提交任何可变患者身份字段。

### 8.2 请求约束

- `/api/chat`
- `/api/chat/stream`
- `/api/chat/history`
- 未来患者挂号相关接口

均不得提交 `patient_id`、`patient_card_id` 或任何等价患者身份字段用于服务端业务判定。

### 8.3 右侧栏挂号触发

当前右侧栏“确认挂号”继续通过聊天/工具链触发挂号，不新增独立前端患者身份参数。身份由后端会话自动注入。

## 9. 数据流

### 9.1 登录

1. 前端提交手机号和验证码
2. 后端按手机号查找或创建 `patient_user_info`
3. 后端返回 `token` 与 `patient_id`
4. 后续所有业务请求通过 `Authorization: Bearer <token>` 标识登录态

### 9.2 聊天

1. 前端发送消息与 `thread_id`
2. 后端从 token 解析 `session.patient_id`
3. 对话历史按 `patient_id + thread_id` 读取和保存
4. Agent 工具从请求上下文获取 `patient_id`

### 9.3 挂号创建

1. 用户在聊天或右侧栏发起挂号意图
2. Agent 工具从 session 中读取 `patient_id`
3. Python HMS client 使用 `patientId` 调用 HMS
4. HMS 将挂号记录写入 `medical_registration.patient_id`

### 9.4 挂号查询与取消

1. 工具从 session 中读取 `patient_id`
2. 查询时仅返回属于该 `patient_id` 的记录
3. 取消前先校验记录归属
4. 校验通过后才允许执行取消

## 10. 错误处理

### 10.1 未登录

以下场景统一返回 `401`：

- 访问聊天接口
- 访问聊天历史接口
- 访问患者档案接口
- 发起挂号相关工具调用但无有效登录态

### 10.2 无权限或记录不存在

查询或取消挂号时：

- 如果记录不存在
- 或记录不属于当前登录患者

统一返回“记录不存在或无权限”，避免暴露其他患者信息。

### 10.3 HMS 失败

HMS 调用失败时：

- 对用户返回现有友好错误提示
- 日志中记录 `patient_id`、接口名和异常摘要

## 11. 迁移顺序

### 11.1 第一步：数据库与 HMS Java 后端

- 修改表结构与 schema
- 修改初始化脚本与测试数据
- 修改 Java form / pojo / dao / mapper / service / controller

### 11.2 第二步：Python Agent 后端

- 修改 HMS client 模型
- 修改挂号服务 payload
- 修改挂号工具与侧栏聚合
- 增加取消前归属校验

### 11.3 第三步：测试

- 更新 Java 测试
- 更新 Python 测试
- 增补“不能取消他人挂号”相关测试

### 11.4 第四步：清理

- 全仓删除残留 `patient_card_id` / `patientCardId`
- 更新架构文档与设计文档

## 12. 测试策略

### 12.1 Java 测试

至少覆盖：

- 创建挂号成功
- 患者不存在
- 排班不存在
- 号源已满
- 查询本人挂号仅返回当前 `patient_id`

### 12.2 Python 后端测试

至少覆盖：

- `/api/chat` 忽略前端伪造 `patient_id`
- `/api/chat/history` 按 `session.patient_id` 隔离
- `create_registration` 无登录态失败
- `query_registration` 只能查当前患者
- `cancel_registration` 无法取消他人挂号

### 12.3 前端验证

- 聊天流和患者相关请求体中不再出现患者身份字段
- 现有登录态和侧栏功能不因字段重命名而失效

## 13. 验收标准

满足以下条件即可视为完成：

1. 仓库中不再存在业务有效引用 `patient_card_id` / `patientCardId`
2. 挂号链路统一使用 `patient_id`
3. 唯一患者身份源为 `patient_user_info.id`
4. 前端与 LLM 均不能自由指定患者身份
5. 聊天、历史、挂号数据均按当前登录患者隔离
6. 取消挂号不能越权操作他人记录
