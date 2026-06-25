# Patient Agent 右侧栏工作台化改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `patient_agent_frontend` 右侧 sidebar 重构为专业医疗工作台风格，同时保持真实接口接线、挂号确认链路和边框稳定性。

**Architecture:** 保持现有 `PatientSidebar -> PatientProfileCard / HospitalScheduleCard` 组件边界，不改后端接口结构，只在现有 sidebar 组件内部重组信息层级、排班交互和视觉样式。默认科室选中逻辑放在 `HospitalScheduleCard` 内部或由 `PatientSidebar` 透传最小状态，样式集中收口到 `src/index.css`，确保所有卡片、导航和弹窗使用稳定盒模型，避免边框和圆角在不同状态下变形。

**Tech Stack:** React 19 + Vite 8 + CSS + lucide-react

## Global Constraints

- 保持右侧栏“上档案、下排班”的大结构不变
- 不改变真实接口结构，不追加前后端字段改造
- 对当前后端 `GET /api/patient/sidebar` 返回结构完全兼容
- 不改聊天主区域
- 不改登录流程
- 不改真实接口结构
- 不改后端字段
- 不改挂号确认后的 `onSendChat(...)` 主链路
- 不新增搜索、筛选、分页、日期切换
- 接口成功时展示真实数据
- 接口失败时展示 mock 数据
- 不因为接口失败导致右侧栏结构错乱
- 所有卡片、字段区、导航项和弹窗边框都必须采用稳定盒模型，避免因内容撑开导致边框拉伸、圆角失真或分隔线错位
- 需要显式校验长医生姓名、长科室名、加载态提示和空态文案下的边框完整性

---

### Task 1: 重构患者档案面板

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes: `profile: { name, gender, age, phone, idCardMasked, recentVisits }`, `loading: boolean`, `loadFailed: boolean`
- Produces:
  - `PatientProfileCard({ profile, loading, loadFailed })`
  - `RecentVisitsList({ visits })`
  - 档案面板主身份区、基础档案区、就诊摘要区对应的稳定类名

- [ ] **Step 1: 重组 `PatientProfileCard.jsx` 的结构**

将 [PatientProfileCard.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx) 改成“主身份区 + 基础档案区 + 就诊摘要区”结构，替换现有松散卡片布局：

```jsx
<section className="patient-card patient-workbench-card">
  <div className="patient-identity-panel">
    <div className="patient-identity-main">
      <div className="patient-identity-name">{profile.name || '--'}</div>
      <div className="patient-identity-tags">
        <span className="patient-status-tag">当前患者</span>
        <span className="patient-status-tag patient-status-tag-muted">已建档</span>
      </div>
    </div>
    <span className="patient-card-badge">
      <ShieldCheck size={12} />
      {loadFailed ? '示例数据' : 'HMS 数据'}
    </span>
  </div>

  <div className="patient-record-grid">
    <div className="patient-record-row">
      <span className="patient-record-key">性别</span>
      <span className="patient-record-value">{profile.gender || '--'}</span>
    </div>
    <div className="patient-record-row">
      <span className="patient-record-key">年龄</span>
      <span className="patient-record-value">{profile.age ? `${profile.age}岁` : '--'}</span>
    </div>
    <div className="patient-record-row">
      <span className="patient-record-key">手机号</span>
      <span className="patient-record-value">{profile.phone || '--'}</span>
    </div>
    <div className="patient-record-row">
      <span className="patient-record-key">身份证尾号</span>
      <span className="patient-record-value">{profile.idCardMasked || '--'}</span>
    </div>
  </div>
```

- [ ] **Step 2: 将 `RecentVisitsList.jsx` 改成业务摘要列表**

在 [RecentVisitsList.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx) 中把每条记录改成“日期主信息 + 科室/医生次信息”的摘要条目：

```jsx
<div className="recent-visit-summary">
  <div className="recent-visit-summary-date">{visit.visitDate}</div>
  <div className="recent-visit-summary-body">
    <span className="recent-visit-summary-dept">{visit.department}</span>
    <span className="recent-visit-summary-divider" />
    <span className="recent-visit-summary-doctor">{visit.doctorName}</span>
  </div>
</div>
```

- [ ] **Step 3: 在 `index.css` 为档案面板补充稳定盒模型样式**

在 [index.css](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/index.css) 中新增并替换 sidebar 相关样式，确保字段区、提示区和记录区都使用固定边框与圆角：

```css
.patient-workbench-card {
  background: #FFFFFF;
  border: 1px solid #D9E2EC;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.patient-identity-panel,
.patient-record-grid,
.patient-visit-section {
  box-sizing: border-box;
}

.patient-record-row {
  min-width: 0;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  background: #F8FBFD;
}
```

- [ ] **Step 4: 运行前端构建验证档案面板改动**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功，且新类名未引入 JSX/CSS 语法错误。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx \
  patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx \
  patient_agent_frontend/src/index.css && \
git commit -m "feat: redesign patient profile workbench panel"
```

### Task 2: 重构科室导航与排班工作区

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes:
  - `HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading })`
  - `DoctorScheduleList({ doctors, onRegister })`
- Produces:
  - 默认选中第一个有排班科室
  - 科室导航条
  - 当前科室排班工作区

- [ ] **Step 1: 在 `HospitalScheduleCard.jsx` 中加入默认科室选中逻辑**

把 [HospitalScheduleCard.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx) 从“手动展开某项”改成“默认选中首个有排班科室”的导航式状态：

```jsx
import { useEffect, useMemo, useState } from 'react'

const firstActiveDeptIndex = useMemo(
  () => departments.findIndex((department) => department.doctors?.length > 0),
  [departments]
)

useEffect(() => {
  if (departments.length === 0) {
    setExpandedDeptIndex(null)
    return
  }
  setExpandedDeptIndex(firstActiveDeptIndex >= 0 ? firstActiveDeptIndex : 0)
}, [departments, firstActiveDeptIndex])
```

- [ ] **Step 2: 将科室切换区改成工作台导航条**

把现有 `.dept-tabs` 输出改成更明确的导航结构，保留数量信息但弱化折叠感：

```jsx
<div className="schedule-dept-nav" role="tablist" aria-label="今日排班科室">
  {departments.map((department, index) => {
    const isActive = expandedDeptIndex === index
    return (
      <button
        key={department.departmentId}
        className={`schedule-dept-nav-item ${isActive ? 'active' : ''}`}
        onClick={() => setExpandedDeptIndex(index)}
      >
        <span className="schedule-dept-nav-name">{department.departmentName}</span>
        <span className="schedule-dept-nav-meta">{department.doctors.length}位</span>
      </button>
    )
  })}
</div>
```

- [ ] **Step 3: 将 `DoctorScheduleList.jsx` 改成业务面板式医生排班项**

在 [DoctorScheduleList.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx) 中调整层级，确保医生主信息、时段标签和按钮分区明确：

```jsx
<div className="doctor-workbench-card">
  <div className="doctor-workbench-main">
    <div className="doctor-workbench-heading">
      <div className="doctor-name">{doctor.doctorName}</div>
      <div className="doctor-title">{doctor.title}</div>
    </div>
    <p className="doctor-bio">{doctor.bio || '暂无医生简介'}</p>
    <div className="doctor-times">
      {doctor.timeSlots.map((slot) => (
        <span key={slot} className="time-slot">{slot}</span>
      ))}
    </div>
  </div>
  <button className="register-btn" onClick={() => onRegister(doctor)}>预约挂号</button>
</div>
```

- [ ] **Step 4: 在 `index.css` 中为导航与排班项补稳定边框样式**

为导航项、医生项、空态占位统一加入固定边框和 `min-width: 0` 约束，避免长科室名和长医生名导致边框变形：

```css
.schedule-dept-nav-item,
.doctor-workbench-card,
.schedule-placeholder,
.schedule-empty {
  box-sizing: border-box;
  min-width: 0;
  border-radius: 12px;
}

.schedule-dept-nav-item {
  border: 1px solid #D9E2EC;
  background: #F8FBFD;
}

.schedule-dept-nav-item.active {
  border-color: #2563EB;
  background: #EFF6FF;
}
```

- [ ] **Step 5: 运行前端构建验证排班区改动**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功，默认科室逻辑和导航重构不引入编译错误。

- [ ] **Step 6: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx \
  patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx \
  patient_agent_frontend/src/index.css && \
git commit -m "feat: redesign hospital schedule workbench"
```

### Task 3: 统一弹窗与状态样式

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes:
  - `RegisterConfirmModal({ user, departmentName, doctor, dateLabel, onCancel, onConfirm })`
  - `PatientSidebar({ user, onSendChat })`
- Produces:
  - 统一工作台风格弹窗
  - 加载态 / fallback 态边框稳定表现

- [ ] **Step 1: 调整 `RegisterConfirmModal.jsx` 的视觉层级**

在 [RegisterConfirmModal.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx) 中保持逻辑不变，只重排结构类名，使其更接近工作台确认框：

```jsx
<div className="modal-card modal-workbench-card" onClick={(event) => event.stopPropagation()}>
  <div className="modal-header modal-workbench-header">
    <span className="modal-title">确认挂号信息</span>
    <button onClick={onCancel} className="modal-close">
      <X size={18} />
    </button>
  </div>
  <div className="modal-body modal-workbench-body">
    ...
  </div>
</div>
```

- [ ] **Step 2: 在 `PatientSidebar.jsx` 中保持 fallback 结构稳定**

检查 [PatientSidebar.jsx](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx)，确保 `sidebar.schedule?.departments || []`、`sidebar.schedule?.dateLabel || scheduleDateLabel` 的 fallback 仍然成立，不再额外引入改变容器宽度的条件渲染。

目标结构：

```jsx
<aside className="patient-sidebar">
  <PatientProfileCard ... />
  <HospitalScheduleCard ... />
</aside>
```

- [ ] **Step 3: 在 `index.css` 中统一 modal / loading / empty 的边框约束**

为弹窗、提示块、空态块补充稳定边框样式，避免加载态和空态让面板边框跳动：

```css
.modal-workbench-card,
.patient-card-hint,
.schedule-loading,
.schedule-placeholder,
.schedule-empty {
  box-sizing: border-box;
  border-radius: 14px;
}

.modal-workbench-card {
  border: 1px solid #D9E2EC;
  background: #FFFFFF;
  overflow: hidden;
}
```

- [ ] **Step 4: 运行前端构建**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功，弹窗与状态样式修改无构建错误。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx \
  patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx \
  patient_agent_frontend/src/index.css && \
git commit -m "feat: unify sidebar workbench states and modal"
```

### Task 4: 完整验证边框与交互

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/*.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes: 已完成的档案面板、排班工作区、弹窗与 fallback 结构
- Produces: 满足 spec 的工作台化右侧栏

- [ ] **Step 1: 运行前端构建总验证**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: PASS，`vite build` 成功。

- [ ] **Step 2: 手工检查边框完整性**

核对以下场景，确认边框、圆角和分隔线都不变形：

```text
1. 接口成功的常规态
2. 接口失败的 fallback 态
3. loading 提示显示时
4. 无排班空态时
5. 长科室名时
6. 长医生姓名/长简介时
7. 打开挂号确认弹窗时
```

- [ ] **Step 3: 手工检查交互链路**

核对以下行为：

```text
1. 默认自动选中第一个有排班科室
2. 切换科室时排班工作区稳定刷新
3. 点击医生后挂号确认弹窗正常显示
4. 确认后仍调用 onSendChat(...)
```

- [ ] **Step 4: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/components/sidebar \
  patient_agent_frontend/src/index.css && \
git commit -m "feat: polish patient sidebar workbench redesign"
```
