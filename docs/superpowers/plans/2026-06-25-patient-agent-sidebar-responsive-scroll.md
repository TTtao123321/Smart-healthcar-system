# Patient Agent Sidebar Responsive Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `patient_agent_frontend` 右侧栏在页面高度变小时的空间分配与滚动问题，使患者档案限高可滚动、医院排班占剩余空间并可完整浏览。

**Architecture:** 保持现有三栏聊天页和右侧双卡片结构不变，只重构右侧栏的纵向 `flex` 分配与内部滚动链路。先用回归测试锁定期望行为，再分别调整患者档案卡片与医院排班卡片的高度协作，最后收口容器样式与验证。

**Tech Stack:** React 19、Vite 8、Vitest、Testing Library、CSS

## Global Constraints

- 不改变现有接口、组件职责和挂号主链路。
- 保持当前视觉语言，不做额外信息折叠和业务字段调整。
- 页面高度变小时，`患者档案` 必须在空间不足时进入内部滚动，而不是继续向下挤压排班区域。
- `医院排班` 必须占用右侧剩余空间，并保持自身可滚动能力。
- 多科室时必须可以完整滚动查看全部科室，多医生时必须可以完整滚动查看全部排班内容。
- 保持 fallback mock 数据兼容。
- 改动范围聚焦在右侧栏，不牵连聊天主区域和左侧栏的既有行为。

---

### Task 1: 锁定小高度响应式回归测试

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: `HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading })`
- Produces: 样式回归断言，覆盖 `.patient-sidebar`、`.patient-profile-scroll`、`.schedule-card`、`.schedule-workbench-panel` 等关键滚动/伸缩规则

- [ ] **Step 1: 写失败测试，描述小高度下的目标布局**

```jsx
it('keeps profile bounded and preserves schedule scrolling rules on short viewports', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={Array.from({ length: 10 }, (_, index) => ({
        departmentId: `dept-${index + 1}`,
        departmentName: `测试科室 ${index + 1}`,
        doctors: [
          {
            doctorId: `doctor-${index + 1}`,
            doctorName: `医生 ${index + 1}`,
            title: '主治医师',
            bio: '用于验证小高度滚动行为的测试数据',
            timeSlots: ['08:00-12:00'],
          },
        ],
      }))}
    />
  )

  expect(appStyles).toMatch(/\.patient-profile-scroll\s*\{[\s\S]*?overflow-y:\s*auto;/)
  expect(appStyles).toMatch(/\.patient-profile-scroll\s*\{[\s\S]*?min-height:\s*0;/)
  expect(appStyles).toMatch(/\.schedule-card\s*\{[\s\S]*?flex:\s*1;/)
  expect(appStyles).toMatch(/\.schedule-workbench-panel\s*\{[\s\S]*?flex:\s*1;/)
})
```

- [ ] **Step 2: 运行单测确认它先失败**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: FAIL，提示缺少 `patient-profile-scroll` 或缺少新的 `flex/overflow` 样式规则。

- [ ] **Step 3: 只保留这次 bug 需要的测试辅助代码**

```jsx
import { readFileSync } from 'node:fs'
import path from 'node:path'

const appStyles = readFileSync(path.resolve(process.cwd(), 'src/index.css'), 'utf8')
```

- [ ] **Step 4: 再跑一次单测，确认仍是“样式未实现”导致失败**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: FAIL，且失败原因集中在新样式断言，而不是语法错误或测试装配错误。

- [ ] **Step 5: 提交测试基线**

```bash
git add patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx
git commit -m "test: add responsive sidebar scroll regression"
```

### Task 2: 给患者档案卡片增加限高与内部滚动容器

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes: `PatientProfileCard({ profile, loading, loadFailed })`
- Produces: `PatientProfileCard` 内部新增 `patient-profile-scroll` 容器；样式上提供限高、内部滚动、低高度压缩规则

- [ ] **Step 1: 先调整结构，让档案卡片拥有独立的可滚动内容容器**

```jsx
export default function PatientProfileCard({ profile, loading, loadFailed }) {
  return (
    <section className="patient-card patient-workbench-card patient-profile-card">
      <div className="patient-profile-scroll">
        <div className="patient-identity-panel">
          ...
        </div>

        {(loading || loadFailed) && (
          <div className="patient-card-state-stack">
            ...
          </div>
        )}

        <div className="patient-record-grid">
          ...
        </div>

        <div className="patient-visit-section">
          ...
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: 为档案卡片补最小 CSS，实现“正常展示 + 空间不足时内部滚动”**

```css
.patient-profile-card {
  flex: 0 1 auto;
  min-height: 0;
  max-height: clamp(260px, 42vh, 420px);
}

.patient-profile-scroll {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
}
```

- [ ] **Step 3: 给小高度场景补克制压缩规则**

```css
@media (max-height: 820px) {
  .patient-card,
  .schedule-card {
    padding: 16px;
  }

  .patient-identity-panel,
  .patient-visit-section {
    margin-bottom: 12px;
    padding-bottom: 12px;
  }

  .patient-record-grid {
    gap: 10px;
  }
}
```

- [ ] **Step 4: 运行回归测试，确认患者档案相关断言转绿**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: PASS 或仅剩医院排班相关断言失败。

- [ ] **Step 5: 提交档案卡片响应式修复**

```bash
git add patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx patient_agent_frontend/src/index.css
git commit -m "fix: bound patient profile card height"
```

### Task 3: 让医院排班卡片稳定吃满剩余空间并补齐滚动链路

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes: `HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading })`
- Produces: 排班卡片作为剩余空间容器；`.schedule-workbench-panel`、`.schedule-dept-nav`、`.schedule-list` 形成完整纵向滚动链路

- [ ] **Step 1: 明确排班卡片结构中的“头部固定 + 主体填充”关系**

```jsx
return (
  <section className="schedule-card schedule-workbench-card">
    <div className="sidebar-header schedule-workbench-header">...</div>
    <div className="schedule-date">{dateLabel}</div>
    {loading && <div className="schedule-loading">正在加载医院排班...</div>}

    <div className="schedule-dept-nav" role="tablist" aria-label="今日排班科室">
      ...
    </div>

    {activeDepartment ? (
      <div className="schedule-workbench-panel">
        <div className="schedule-current-dept">...</div>
        <DoctorScheduleList doctors={activeDepartment.doctors} onRegister={setConfirmDoctor} />
      </div>
    ) : (
      ...
    )}
  </section>
)
```

- [ ] **Step 2: 用最小 CSS 让排班卡片吃满右侧剩余空间**

```css
.patient-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.schedule-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.schedule-workbench-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
```

- [ ] **Step 3: 补齐科室导航和医生列表的滚动链路**

```css
.schedule-dept-nav {
  flex: 0 1 220px;
  min-height: 0;
  overflow-y: auto;
}

.schedule-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
```

- [ ] **Step 4: 跑单测并确认整套响应式断言通过**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: PASS，右侧栏响应式相关测试全部通过。

- [ ] **Step 5: 提交排班区剩余空间与滚动修复**

```bash
git add patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx patient_agent_frontend/src/components/sidebar/DoctorScheduleList.jsx patient_agent_frontend/src/index.css
git commit -m "fix: preserve schedule area on short viewports"
```

### Task 4: 收口容器样式并做完整验证

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`
- Modify: `patient_agent_frontend/src/index.css`
- Test: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: 任务 2 和任务 3 产出的卡片级滚动规则
- Produces: 右侧整列最终响应式行为；完整验证证据

- [ ] **Step 1: 只在必要时收口右侧容器样式，避免外层与内层滚动冲突**

```css
.patient-sidebar {
  width: 300px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}
```

- [ ] **Step 2: 如容器无需额外逻辑，保持 `PatientSidebar.jsx` 仅承载结构，不新增业务代码**

```jsx
return (
  <aside className="patient-sidebar">
    <PatientProfileCard
      profile={{ ...sidebar.profile, recentVisits: sidebar.recentVisits }}
      loading={loading}
      loadFailed={loadFailed}
    />
    <HospitalScheduleCard
      user={user}
      onSendChat={onSendChat}
      departments={sidebar.schedule?.departments || []}
      dateLabel={sidebar.schedule?.dateLabel || scheduleDateLabel}
      loading={loading}
    />
  </aside>
)
```

- [ ] **Step 3: 跑前端测试全集**

Run: `npm test`  
Expected: PASS，`patient_agent_frontend` 测试全部通过。

- [ ] **Step 4: 跑生产构建验证样式改动未破坏打包**

Run: `npm run build`  
Expected: PASS，Vite 构建成功，无新的构建错误。

- [ ] **Step 5: 提交最终收口**

```bash
git add patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx patient_agent_frontend/src/index.css patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx
git commit -m "fix: stabilize responsive sidebar scrolling"
```
