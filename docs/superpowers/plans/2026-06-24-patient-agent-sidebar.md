# Patient Agent 右侧栏拆分 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `patient_agent_frontend` 聊天页右侧栏从单一“今日排班”模块拆分为“患者信息与近期就诊记录” + “医院排班”两块，并为后续 HMS 对接预留清晰的数据结构与组件边界。

**Architecture:** 保持现有三栏聊天页布局不变，仅重构右侧栏。通过新增 `sidebar` 组件目录和独立 mock 数据文件，把当前 `App.jsx` 中的 `RightPanel` 单体实现拆为组合容器、患者信息卡、近期就诊记录列表、医院排班卡、医生列表和挂号确认弹窗。`App.jsx` 只保留挂载和聊天发送接线，排班确认仍沿用 `onSendChat(...)` 将挂号意图发回聊天主流程。

**Tech Stack:** React 19 + Vite 8 + lucide-react + 现有 `index.css`

## Global Constraints

- 仅修改 `patient_agent_frontend`，不开发后端接口
- 保持聊天页三栏布局不变，不引入路由
- 右侧上方展示 `姓名 / 性别 / 年龄 / 手机号 / 身份证号后四位`
- 上方同时展示最近 `3` 条就诊记录，字段为 `就诊日期 / 科室 / 医生`
- 下方排班继续支持“点击科室展开”“预约挂号确认弹窗”“确认后调用 `onSendChat(...)`”
- 继续使用 `lucide-react` 图标和现有 `index.css` 风格体系
- 允许新增组件和 mock 数据文件，但不要重构聊天主流程

---

### Task 1: 提取右侧栏 mock 数据与组件骨架

**Files:**
- Create: `patient_agent_frontend/src/mocks/patientProfile.js`
- Create: `patient_agent_frontend/src/mocks/scheduleData.js`
- Create: `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`
- Create: `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx`
- Create: `patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx`
- Create: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Create: `patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx`
- Create: `patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx`

**Interfaces:**
- Consumes: `lucide-react` 图标；`onSendChat(message: string)`；`user: { name: string }`
- Produces:
  - `patientProfile: PatientProfile`
  - `scheduleDepartments: ScheduleDepartment[]`
  - `PatientSidebar({ user, onSendChat })`
  - `PatientProfileCard({ profile })`
  - `RecentVisitsList({ visits })`
  - `HospitalScheduleCard({ user, onSendChat, departments, dateLabel })`

- [ ] **Step 1: 创建患者信息 mock 数据文件**

新建 `patient_agent_frontend/src/mocks/patientProfile.js`：

```js
export const patientProfile = {
  patientId: 'patient-demo-001',
  name: '王小雨',
  gender: '女',
  age: 29,
  phone: '138****1024',
  idCardMasked: '1024',
  recentVisits: [
    {
      visitId: 'visit-001',
      visitDate: '2026-06-18',
      department: '呼吸内科',
      doctorName: '李芳',
    },
    {
      visitId: 'visit-002',
      visitDate: '2026-05-30',
      department: '全科门诊',
      doctorName: '张明华',
    },
    {
      visitId: 'visit-003',
      visitDate: '2026-04-12',
      department: '消化内科',
      doctorName: '陈志远',
    },
  ],
}
```

- [ ] **Step 2: 创建医院排班 mock 数据文件**

新建 `patient_agent_frontend/src/mocks/scheduleData.js`：

```js
export const scheduleDateLabel = '2026年6月24日 周三'

export const scheduleDepartments = [
  {
    departmentId: 'dept-internal',
    departmentName: '内科',
    doctors: [
      {
        doctorId: 'doctor-001',
        doctorName: '张明华',
        title: '主任医师',
        bio: '擅长心血管疾病诊疗，30年临床经验',
        departmentName: '内科',
        timeSlots: ['08:00-12:00', '14:00-17:00'],
      },
      {
        doctorId: 'doctor-002',
        doctorName: '李芳',
        title: '副主任医师',
        bio: '呼吸系统疾病专家，擅长慢性病管理',
        departmentName: '内科',
        timeSlots: ['08:00-12:00'],
      },
    ],
  },
]
```

- [ ] **Step 3: 创建 `RecentVisitsList` 组件**

新建 `patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx`：

```jsx
export default function RecentVisitsList({ visits }) {
  if (!visits || visits.length === 0) {
    return <div className="recent-visits-empty">暂无近期就诊记录</div>
  }

  return (
    <div className="recent-visits-list">
      {visits.slice(0, 3).map((visit) => (
        <div key={visit.visitId} className="recent-visit-item">
          <div className="recent-visit-date">{visit.visitDate}</div>
          <div className="recent-visit-meta">
            <span>{visit.department}</span>
            <span>{visit.doctorName}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: 创建 `PatientProfileCard` 组件**

新建 `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx`：

```jsx
import { UserCircle, ClipboardList } from 'lucide-react'
import RecentVisitsList from './RecentVisitsList.jsx'

export default function PatientProfileCard({ profile }) {
  return (
    <section className="patient-card">
      <div className="patient-card-header">
        <UserCircle size={18} className="text-sky" />
        <span>个人信息</span>
      </div>

      <div className="patient-profile-grid">
        <div className="patient-profile-item">
          <span className="patient-profile-label">姓名</span>
          <span className="patient-profile-value">{profile.name}</span>
        </div>
        <div className="patient-profile-item">
          <span className="patient-profile-label">性别</span>
          <span className="patient-profile-value">{profile.gender}</span>
        </div>
        <div className="patient-profile-item">
          <span className="patient-profile-label">年龄</span>
          <span className="patient-profile-value">{profile.age}岁</span>
        </div>
        <div className="patient-profile-item">
          <span className="patient-profile-label">手机号</span>
          <span className="patient-profile-value">{profile.phone}</span>
        </div>
        <div className="patient-profile-item patient-profile-item-wide">
          <span className="patient-profile-label">身份证尾号</span>
          <span className="patient-profile-value">{profile.idCardMasked}</span>
        </div>
      </div>

      <div className="patient-visit-section">
        <div className="patient-visit-header">
          <ClipboardList size={16} className="text-purple" />
          <span>近期就诊记录</span>
        </div>
        <RecentVisitsList visits={profile.recentVisits} />
      </div>
    </section>
  )
}
```

- [ ] **Step 5: 创建 `DoctorScheduleList` 组件**

新建 `patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx`：

```jsx
import { Clock } from 'lucide-react'

export default function DoctorScheduleList({ doctors, onRegister }) {
  if (!doctors || doctors.length === 0) {
    return <div className="schedule-empty">今日暂无排班</div>
  }

  return (
    <div className="schedule-list">
      {doctors.map((doctor) => (
        <div key={doctor.doctorId} className="doctor-card">
          <div className="doctor-header">
            <div className="doctor-avatar">{doctor.doctorName[0]}</div>
            <div className="doctor-info">
              <div className="doctor-name">{doctor.doctorName}</div>
              <div className="doctor-title">{doctor.title}</div>
            </div>
          </div>
          <p className="doctor-bio">{doctor.bio}</p>
          <div className="doctor-times">
            <Clock size={13} className="text-sky" />
            {doctor.timeSlots.map((slot) => (
              <span key={slot} className="time-slot">{slot}</span>
            ))}
          </div>
          <button className="register-btn" onClick={() => onRegister(doctor)}>
            预约挂号
          </button>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 6: 创建挂号弹窗和排班卡组件**

新建 `patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx`：

```jsx
import { X } from 'lucide-react'

export default function RegisterConfirmModal({ user, departmentName, doctor, dateLabel, onCancel, onConfirm }) {
  if (!doctor) return null

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">确认挂号信息</span>
          <button onClick={onCancel} className="modal-close">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">
          <div className="modal-row">
            <span className="modal-label">就诊日期</span>
            <span className="modal-value">{dateLabel}</span>
          </div>
          <div className="modal-row">
            <span className="modal-label">就诊患者</span>
            <span className="modal-value">{user.name}</span>
          </div>
          <div className="modal-row">
            <span className="modal-label">就诊科室</span>
            <span className="modal-value">{departmentName}</span>
          </div>
          <div className="modal-row">
            <span className="modal-label">接诊医生</span>
            <span className="modal-value">{doctor.doctorName}（{doctor.title}）</span>
          </div>
        </div>
        <div className="modal-footer">
          <button onClick={onCancel} className="modal-btn modal-btn-cancel">取消</button>
          <button onClick={onConfirm} className="modal-btn modal-btn-confirm">确认挂号</button>
        </div>
      </div>
    </div>
  )
}
```

新建 `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`：

```jsx
import { useState } from 'react'
import { Calendar, Stethoscope } from 'lucide-react'
import DoctorScheduleList from './DoctorScheduleList.jsx'
import RegisterConfirmModal from './RegisterConfirmModal.jsx'

export default function HospitalScheduleCard({ user, onSendChat, departments, dateLabel }) {
  const [expandedDept, setExpandedDept] = useState(null)
  const [confirmDoctor, setConfirmDoctor] = useState(null)

  const activeDepartment = expandedDept === null ? null : departments[expandedDept]

  const handleConfirm = () => {
    if (!activeDepartment || !confirmDoctor) return
    onSendChat(`我要预约挂号：${activeDepartment.departmentName} · ${confirmDoctor.doctorName}（${confirmDoctor.title}）`)
    setConfirmDoctor(null)
  }

  return (
    <section className="schedule-card">
      <div className="sidebar-header">
        <Calendar size={18} className="text-sky" />
        <span>医院排班</span>
      </div>
      <div className="schedule-date">{dateLabel}</div>
      <div className="dept-tabs">
        {departments.map((department, index) => (
          <button
            key={department.departmentId}
            className={`dept-tab ${expandedDept === index ? 'active' : ''}`}
            onClick={() => setExpandedDept(expandedDept === index ? null : index)}
          >
            <Stethoscope size={14} />
            <span>{department.departmentName}</span>
            <span className="dept-count">{department.doctors.length}位</span>
          </button>
        ))}
      </div>

      {activeDepartment ? (
        <DoctorScheduleList doctors={activeDepartment.doctors} onRegister={setConfirmDoctor} />
      ) : (
        <div className="schedule-placeholder">点击具体科室查看排班信息</div>
      )}

      <RegisterConfirmModal
        user={user}
        departmentName={activeDepartment?.departmentName || ''}
        doctor={confirmDoctor}
        dateLabel={dateLabel}
        onCancel={() => setConfirmDoctor(null)}
        onConfirm={handleConfirm}
      />
    </section>
  )
}
```

- [ ] **Step 7: 创建 `PatientSidebar` 组合容器**

新建 `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`：

```jsx
import PatientProfileCard from './PatientProfileCard.jsx'
import HospitalScheduleCard from './HospitalScheduleCard.jsx'
import { patientProfile } from '../../mocks/patientProfile.js'
import { scheduleDateLabel, scheduleDepartments } from '../../mocks/scheduleData.js'

export default function PatientSidebar({ user, onSendChat }) {
  return (
    <aside className="patient-sidebar">
      <PatientProfileCard profile={patientProfile} />
      <HospitalScheduleCard
        user={user}
        onSendChat={onSendChat}
        departments={scheduleDepartments}
        dateLabel={scheduleDateLabel}
      />
    </aside>
  )
}
```

- [ ] **Step 8: 验证新文件导入语法**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: 构建流程结束；若样式类尚未补齐，允许仅出现样式缺失，不应出现模块导入或 JSX 语法错误。

- [ ] **Step 9: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/mocks/patientProfile.js \
  patient_agent_frontend/src/mocks/scheduleData.js \
  patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx \
  patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx \
  patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx \
  patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx \
  patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx \
  patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx && \
git commit -m "feat: split patient sidebar data and components"
```

### Task 2: 用新侧栏替换 `App.jsx` 中的 `RightPanel`

**Files:**
- Modify: `patient_agent_frontend/src/App.jsx`

**Interfaces:**
- Consumes: `PatientSidebar({ user, onSendChat })`
- Produces: `ChatPage` 使用新右侧栏；旧 `RightPanel` 和内联 `scheduleData` 被移除

- [ ] **Step 1: 替换顶部图标与组件导入**

修改 `patient_agent_frontend/src/App.jsx` 顶部 import：

```jsx
import PatientSidebar from './components/sidebar/PatientSidebar.jsx'
```

将原 `lucide-react` 导入中的：

```jsx
Calendar, Clock, Stethoscope, ChevronDown, ChevronUp, X,
```

替换为：

```jsx
ChevronDown, ChevronUp,
```

因为 `RightPanel` 被完整删除，`App.jsx` 不再直接使用 `Calendar`、`Clock`、`Stethoscope`、`X`，这些图标需要从 `App.jsx` 的导入列表中一并移除。

- [ ] **Step 2: 在 `ChatPage` 中替换右侧栏挂载**

将 `ChatPage` return 中的：

```jsx
<RightPanel user={user} onSendChat={handleSend} />
```

替换为：

```jsx
<PatientSidebar user={user} onSendChat={handleSend} />
```

- [ ] **Step 3: 删除旧 `RightPanel` 与内联 `scheduleData`**

删除 `App.jsx` 中整段旧实现：

```jsx
function RightPanel({ user, onSendChat }) {
  // ...
}

const scheduleData = [
  // ...
]
```

删除后，`App.jsx` 只保留聊天页、登录页、消息列表和工具调用展示相关逻辑。

- [ ] **Step 4: 运行构建验证替换完成**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功，不再出现 `RightPanel` 或 `scheduleData` 未定义错误。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/App.jsx && git commit -m "refactor: replace inline right panel with patient sidebar"
```

### Task 3: 为新右侧栏补齐样式并保持现有视觉体系

**Files:**
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes: `patient-sidebar`、`patient-card`、`recent-visits-list`、`schedule-card` 等类名
- Produces: 上下双卡片布局、患者信息栅格、近期就诊记录列表、排班卡和空状态样式

- [ ] **Step 1: 在侧栏区域新增组合容器样式**

在 `patient_agent_frontend/src/index.css` 的 sidebar 样式区之后追加：

```css
.patient-sidebar {
  width: 300px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.patient-card,
.schedule-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  padding: 20px;
}
```

- [ ] **Step 2: 添加患者信息与近期就诊记录样式**

在 `index.css` 中追加：

```css
.patient-profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.patient-profile-item {
  padding: 12px;
  border-radius: 12px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
}

.patient-profile-item-wide {
  grid-column: 1 / -1;
}

.patient-profile-label {
  display: block;
  font-size: 11px;
  color: #64748B;
  margin-bottom: 6px;
}

.patient-profile-value {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
}

.patient-visit-section {
  padding-top: 12px;
  border-top: 1px solid #E2E8F0;
}

.recent-visits-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-visit-item {
  padding: 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #F8FAFC, #F1F5F9);
}
```

- [ ] **Step 3: 添加排班卡与空状态补充样式**

在 `index.css` 现有排班区样式附近补充：

```css
.schedule-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.schedule-empty,
.schedule-placeholder,
.recent-visits-empty {
  color: #94A3B8;
  font-size: 13px;
  text-align: center;
}

.schedule-placeholder {
  padding: 32px 20px;
  border-radius: 12px;
  background: #F8FAFC;
  border: 1px dashed #CBD5E1;
}
```

- [ ] **Step 4: 运行构建验证样式类完整**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功，页面类名和 JSX 匹配，不出现未使用导入导致的构建错误。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/index.css && git commit -m "style: add patient sidebar card and schedule styles"
```

### Task 4: 进行最终验证并清理收尾

**Files:**
- Modify: `patient_agent_frontend/src/App.jsx`
- Modify: `patient_agent_frontend/src/index.css`
- Modify: `patient_agent_frontend/src/components/sidebar/*.jsx`

**Interfaces:**
- Consumes: 已完成的右侧栏组件、样式和 mock 数据
- Produces: 可构建、可交互、无明显诊断错误的前端实现

- [ ] **Step 1: 运行最终构建**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: 输出 `dist/`，构建成功。

- [ ] **Step 2: 检查最近修改文件诊断**

检查文件：

```text
patient_agent_frontend/src/App.jsx
patient_agent_frontend/src/index.css
patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx
patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx
patient_agent_frontend/src/components/sidebar/RecentVisitsList.jsx
patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx
patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx
patient_agent_frontend/src/components/sidebar/RegisterConfirmModal.jsx
patient_agent_frontend/src/mocks/patientProfile.js
patient_agent_frontend/src/mocks/scheduleData.js
```

Expected: 无明显 import 错误、未定义变量错误或 JSX 语法错误。

- [ ] **Step 3: 手动核对交互**

核对以下行为：

```text
1. 右侧顶部显示个人信息卡
2. 个人信息卡底部显示最近 3 条就诊记录
3. 右侧底部显示医院排班卡
4. 点击科室后展示医生卡片
5. 点击“预约挂号”后弹出确认框
6. 点击“确认挂号”后仍走 onSendChat(...)
```

- [ ] **Step 4: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/App.jsx \
  patient_agent_frontend/src/index.css \
  patient_agent_frontend/src/components/sidebar \
  patient_agent_frontend/src/mocks && \
git commit -m "feat: split patient sidebar into profile and hospital schedule modules"
```
