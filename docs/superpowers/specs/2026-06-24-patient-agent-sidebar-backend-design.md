# patient_agent 右侧栏后端对接设计

**日期：** 2026-06-24
**范围：** `patient_agent_backend`、`patient_agent_frontend`
**状态：** 已确认

## 概述

本次改造目标是在已完成的 `patient_agent_frontend` 右侧栏拆分基础上，为“个人信息 + 近期就诊记录 + 医院排班”三块内容接入真实后端数据。

前端不再直接使用本地 mock 作为主数据源，而是统一通过 `patient_agent_backend` 获取侧栏聚合结果。`patient_agent_backend` 负责结合当前登录患者身份，聚合患者档案、最近就诊流水和当日医院排班，并把数据转换为前端侧栏所需的稳定结构。

本次目标是打通“右侧栏展示数据”的后端链路，不改变聊天主流程，不改变挂号确认后继续走 `onSendChat(...)` 的交互方式。

## 当前现状

### 前端现状

`patient_agent_frontend` 右侧栏已经拆分为以下组件：

- `PatientSidebar`
- `PatientProfileCard`
- `RecentVisitsList`
- `HospitalScheduleCard`
- `DoctorScheduleList`
- `RegisterConfirmModal`

当前数据来源仍是前端 mock：

- `src/mocks/patientProfile.js`
- `src/mocks/scheduleData.js`

这意味着右侧栏虽然已经具备可接入真实数据的组件边界，但尚未接入真实接口。

### 后端现状

`patient_agent_backend` 已有患者档案能力：

- `GET /api/patient/profile`
- `POST /api/patient/profile`

患者档案实际数据来自 `patient_user_info`，且当前登录态已经能拿到真实 `patient_id`。

`hospital_manage_backend` 已有与患者流水和医院排班相关的业务接口，但 `patient_agent_backend` 当前没有为右侧栏提供专门的聚合接口：

- 患者详情与挂号流水：`/patient/selectDetail`、`/patient/selectByPage`
- 科室：`/medical/dept/selectAllDeptNameAndId`
- 诊室：`/medical/dept/sub/selectByDeptId`
- 医生：`/doctor/selectDoctorsBySubId`
- 排班：`/doctor/work_plan/schedule/selectDoctorScheduleByDeptSubIdAndDate`

因此，本次需要在 `patient_agent_backend` 新增专门面向右侧栏的聚合能力。

## 设计目标

### 业务目标

- 让右侧栏展示当前登录患者的真实基础信息
- 让右侧栏展示最近 `3` 条真实挂号/就诊流水
- 让右侧栏展示当天真实医院排班
- 在不改变现有聊天与挂号交互的前提下，完成侧栏展示数据的真实化

### 技术目标

- 保持 `patient_agent_frontend -> patient_agent_backend -> HMS` 的分层
- 前端只请求一个聚合接口，不在前端拼装多路业务数据
- 在 `patient_agent_backend` 完成鉴权、字段适配、脱敏与格式转换
- 尽量复用现有 HMS 接口，不优先扩展 `hospital_manage_backend`

## 方案选择

本次采用“`patient_agent_backend` 新增侧栏聚合接口”的方案。

### 采用方案

- 新增 `GET /api/patient/sidebar`
- 前端右侧栏只调用这一个接口
- `patient_agent_backend` 内部聚合：
  - 当前登录患者档案
  - 最近 `3` 条挂号/就诊流水
  - 当日医院排班
- 聚合结果按前端右侧栏当前组件期望的结构返回

### 不采用的方案

- 不采用“前端直连 HMS”的方案，因为会把鉴权、脱敏、格式转换散落到前端
- 不采用“前端多接口拼装”的方案，因为会增加前端状态复杂度和错误处理成本
- 不采用“先改 HMS 新增专用 sidebar 接口”的方案，因为当前已有接口基本可支撑，优先减少跨仓改动范围

## 接口设计

### 新增接口

`GET /api/patient/sidebar`

### 认证要求

- 必须要求患者已登录
- 从 `Authorization: Bearer <token>` 解析真实 `patient_id`
- 不信任前端透传的 `patient_id`

### 返回结构

```json
{
  "profile": {
    "patientId": "123",
    "name": "张三",
    "gender": "男",
    "age": 29,
    "phone": "138****1024",
    "idCardMasked": "1024"
  },
  "recentVisits": [
    {
      "visitId": "reg-001",
      "visitDate": "2026-06-18",
      "department": "呼吸内科",
      "doctorName": "李芳"
    }
  ],
  "schedule": {
    "dateLabel": "2026年6月24日 周三",
    "departments": [
      {
        "departmentId": "dept-001",
        "departmentName": "内科",
        "doctors": [
          {
            "doctorId": "doc-001",
            "doctorName": "张明华",
            "title": "主任医师",
            "bio": "擅长心血管疾病诊疗，30年临床经验",
            "departmentName": "内科",
            "timeSlots": ["08:00-12:00", "14:00-17:00"]
          }
        ]
      }
    ]
  }
}
```

## 数据来源与字段映射

### 一、患者基础信息

患者基础信息来源于 `patient_agent_backend` 当前已接入的 `patient_user_info`。

#### 来源字段

- `id`
- `name`
- `sex`
- `pid`
- `tel`
- `birthday`

#### 映射规则

- `patientId <- id`
- `name <- name`
- `gender <- sex`
- `age <- birthday` 计算年龄
- `phone <- tel` 脱敏后返回
- `idCardMasked <- pid` 取后四位

#### 处理要求

- 若 `birthday` 为空，则 `age` 返回 `null` 或前端可接受的空值
- 若 `pid` 长度不足 4 位，则保底返回原值或空字符串
- 后端统一完成手机号脱敏与身份证尾号提取，前端不自行处理隐私字段

### 二、近期就诊记录

本次“近期就诊记录”采用真实的挂号/就诊流水，不采用病历摘要。

#### 数据来源

优先复用 HMS 侧患者详情或挂号流水能力：

- `/patient/selectDetail`
- 或 `/patient/selectByPage`

推荐优先使用能直接按当前患者身份拿到就诊流水的实现，并在 `patient_agent_backend` 中适配为轻量记录列表。

#### 目标字段

- `visitId`
- `visitDate`
- `department`
- `doctorName`

#### 映射规则

- `visitId <- registrationId`
- `visitDate <- date`
- `department <- deptSubName`，若为空则退回 `deptName`
- `doctorName <- doctorName`

#### 处理要求

- 只返回最近 `3` 条记录
- 按日期倒序排列
- 不返回诊断、检查、处方等病历型字段

### 三、医院排班

医院排班由 `patient_agent_backend` 基于 HMS 现有科室、诊室、医生与排班接口做聚合。

#### 数据来源

- 科室：`/medical/dept/selectAllDeptNameAndId`
- 诊室：`/medical/dept/sub/selectByDeptId`
- 医生：`/doctor/selectDoctorsBySubId`
- 排班：`/doctor/work_plan/schedule/selectDoctorScheduleByDeptSubIdAndDate`

#### 目标字段

- `dateLabel`
- `departments[].departmentId`
- `departments[].departmentName`
- `departments[].doctors[].doctorId`
- `departments[].doctors[].doctorName`
- `departments[].doctors[].title`
- `departments[].doctors[].bio`
- `departments[].doctors[].departmentName`
- `departments[].doctors[].timeSlots`

#### 映射规则

- `departmentId <- medical_dept.id`
- `departmentName <- medical_dept.name`
- `doctorId <- doctor.id`
- `doctorName <- doctor.name`
- `title <- doctor.job`
- `bio <- doctor.description`
- `departmentName <- medical_dept.name`
- `timeSlots <- doctor_work_plan / doctor_work_plan_schedule` 转换为前端展示字符串数组

#### 时段转换要求

HMS 当前排班接口返回的更接近 slot 编号或布尔位数组，而不是前端展示用的字符串时段。因此需要在 `patient_agent_backend` 中做统一转换，例如：

- `上午`
- `下午`
- 或具体时间段字符串

最终输出必须保持为前端当前组件可直接渲染的 `string[]`。

## 模块设计

### patient_agent_backend

建议新增或扩展以下结构：

```text
app/
├── api/
│   └── patient.py
├── patient_sidebar/
│   ├── models.py
│   ├── service.py
│   └── adapters.py
```

#### `api/patient.py`

新增：

- `GET /api/patient/sidebar`

职责：

- 从登录态取当前患者身份
- 调用 `patient_sidebar.service`
- 返回统一侧栏响应

#### `patient_sidebar/service.py`

职责：

- 协调患者档案、近期就诊记录、医院排班三部分数据
- 控制失败降级策略
- 输出最终聚合结果

#### `patient_sidebar/adapters.py`

职责：

- 将 `patient_user_info` 转换为 `profile`
- 将 HMS 挂号/就诊流水转换为 `recentVisits`
- 将 HMS 科室/医生/排班数据转换为 `schedule`
- 统一处理脱敏、年龄计算、时段格式化

### patient_agent_frontend

前端只需要将当前 mock 数据入口切换为真实接口请求：

- `PatientSidebar` 负责请求 `GET /api/patient/sidebar`
- 各子组件继续接收解耦后的展示数据
- mock 可保留为开发 fallback，但真实环境以接口数据为准

## 错误处理

### 登录态错误

- 未登录访问 `GET /api/patient/sidebar`：返回 `401`
- 前端沿用现有登录态失效逻辑

### 聚合错误策略

- `profile` 查询失败：接口整体失败，不返回半残基础档案
- `recentVisits` 查询失败：降级为空数组
- `schedule` 查询失败：降级为 `dateLabel + 空 departments`

### 字段缺失处理

- HMS 缺少科室名、医生名、说明字段时，统一返回空字符串或 `--`
- 不允许把底层不稳定结构直接暴露给前端

## 前端对接方式

### 请求方式

新增或扩展患者侧 API：

- `GET /api/patient/sidebar`

### 前端状态变化

- `PatientSidebar` 在挂载时请求侧栏数据
- 加载中显示 skeleton 或轻量占位
- 成功后替换当前 mock
- 失败时显示空态或错误提示

### 保持不变的行为

- 右侧挂号确认弹窗逻辑保持不变
- 确认后继续调用 `onSendChat(...)`
- 聊天主链路与 thread 逻辑不变

## 本次范围

### 本次要做

- `patient_agent_backend` 新增侧栏聚合接口
- `patient_agent_backend` 增加侧栏适配与聚合逻辑
- `patient_agent_frontend` 将右侧栏切到真实接口
- 近期就诊记录改用真实挂号/就诊流水
- 医院排班改用真实 HMS 聚合结果

### 本次不做

- 不做患者信息编辑
- 不做“查看更多近期记录”
- 不做排班日期切换
- 不改变挂号确认后的聊天交互
- 不优先修改 `hospital_manage_backend`，除非联调证明现有接口不足以支撑

## 验证方式

### 后端验证

- `GET /api/patient/sidebar` 在已登录状态下返回完整结构
- 未登录访问返回 `401`
- `recentVisits` 最多返回 `3` 条
- `phone` 已脱敏
- `idCardMasked` 只返回身份证后四位
- 排班为空时接口仍返回成功，`schedule.departments` 可为空数组

### 前端验证

- 登录后右侧栏使用真实接口数据渲染
- 上方显示真实患者信息和最近 `3` 条记录
- 下方显示真实医院排班
- 排班为空时，个人信息仍正常显示
- 点击医生后挂号确认弹窗仍正常工作

### 联调验证

- 真实登录患者进入页面
- 看到个人信息、近期记录、医院排班三块真实内容
- 右侧栏结构和交互与前端已完成的布局一致

## 风险与兼容性

### 风险点

- HMS 排班接口返回结构与前端展示字段不完全一致，需要在 `patient_agent_backend` 做转换
- 近期就诊记录可能依赖患者卡号或 HMS 内部患者主键映射，需要确认与当前 `patient_id` 的对应关系
- 若现有 HMS 接口无法稳定支撑“按当前登录患者直接查最近流水”，可能需要补一层 patient_agent 侧查询适配

### 兼容性说明

- 前端组件边界已经按真实接口形态设计，本次主要替换数据源
- mock 可以保留为本地开发兜底，不影响生产接口接入
- 若 HMS 某部分数据暂时不可用，侧栏应尽量部分可用，而不是整体白屏

## 实施顺序

1. 为 `patient_agent_backend` 设计并实现 `GET /api/patient/sidebar`
2. 实现 `profile` 映射、年龄计算、隐私字段脱敏
3. 接入最近 `3` 条挂号/就诊流水并适配为 `recentVisits`
4. 接入当日医院排班并适配为 `schedule`
5. 改造 `patient_agent_frontend`，将右侧栏从 mock 切到真实接口
6. 完成后端接口验证与前端联调
