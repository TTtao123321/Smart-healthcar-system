# Patient Agent Current Department Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将医院排班模块中的“当前科室”区域升级为当前科室摘要卡，展示科室简介、上午号源数量、下午号源数量，并保持排班模块在小高度下可滚动浏览。

**Architecture:** 保持 `HospitalScheduleCard` 当前结构不变，在前端基于 `activeDepartment.doctors` 和 `timeSlots` 推导摘要数据，不扩展后端接口。先通过测试锁定推导规则和 UI 期望，再补最小实现和样式，最后做完整验证。

**Tech Stack:** React 19、Vite 8、Vitest、Testing Library、CSS

## Global Constraints

- 保留当前科室信息区的位置，不新增折叠或切换交互。
- 前端直接基于当前已拿到的 `doctors` 和 `timeSlots` 推导展示数据。
- 当前科室摘要卡仍属于医院排班模块内部内容，并随排班模块一起可滚动浏览。
- 不修改挂号主链路，不增加额外交互状态。
- 统计口径固定为“可挂号时段数量”，不包装成真实库存概念。
- 简介缺失时必须显示 `暂无科室简介`。
- 不破坏现有科室切换和挂号确认流程。

---

### Task 1: 锁定当前科室摘要卡的推导与展示测试

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`
- Modify: `patient_agent_frontend/src/mocks/scheduleData.js`

**Interfaces:**
- Consumes: `HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading })`
- Produces: 当前科室简介、上午/下午号源数量、排班模块滚动样式的回归测试

- [ ] **Step 1: 为 mock 数据补足可稳定统计上午/下午时段的样本**

```js
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
        timeSlots: ['08:30-11:30'],
      },
    ],
  },
]
```

- [ ] **Step 2: 写失败测试，断言当前科室摘要卡展示推导结果**

```jsx
it('shows the selected department summary with intro and morning afternoon slot counts', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={[
        {
          departmentId: 'dept-internal',
          departmentName: '内科',
          doctors: [
            {
              doctorId: 'doctor-001',
              doctorName: '张明华',
              title: '主任医师',
              bio: '擅长心血管疾病诊疗，30年临床经验',
              timeSlots: ['08:00-12:00', '14:00-17:00'],
            },
            {
              doctorId: 'doctor-002',
              doctorName: '李芳',
              title: '副主任医师',
              bio: '呼吸系统疾病专家，擅长慢性病管理',
              timeSlots: ['08:30-11:30'],
            },
          ],
        },
      ]}
    />
  )

  expect(screen.getByText('内科')).toBeInTheDocument()
  expect(screen.getByText(/擅长心血管疾病诊疗/)).toBeInTheDocument()
  expect(screen.getByText('上午号源')).toBeInTheDocument()
  expect(screen.getByText('2')).toBeInTheDocument()
  expect(screen.getByText('下午号源')).toBeInTheDocument()
  expect(screen.getByText('1')).toBeInTheDocument()
})
```

- [ ] **Step 3: 补一条简介缺失兜底断言**

```jsx
it('falls back to default department intro when doctor bios are missing', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={[
        {
          departmentId: 'dept-empty',
          departmentName: '全科门诊',
          doctors: [
            {
              doctorId: 'doctor-003',
              doctorName: '王医生',
              title: '主治医师',
              bio: '',
              timeSlots: [],
            },
          ],
        },
      ]}
    />
  )

  expect(screen.getByText('暂无科室简介')).toBeInTheDocument()
})
```

- [ ] **Step 4: 运行单测确认它先失败**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: FAIL，原因是当前科室摘要卡尚未显示简介和上午/下午号源数量。

- [ ] **Step 5: 提交测试基线**

```bash
git add patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx patient_agent_frontend/src/mocks/scheduleData.js
git commit -m "test: cover current department summary card"
```

### Task 2: 在 HospitalScheduleCard 中补前端推导逻辑

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`

**Interfaces:**
- Consumes: `activeDepartment: { departmentName: string, doctors: Array<{ bio?: string, timeSlots?: string[] }> }`
- Produces: `departmentSummary = { intro: string, morningCount: number, afternoonCount: number }`

- [ ] **Step 1: 在组件顶部新增一个本地纯函数，用于推导摘要数据**

```jsx
function buildDepartmentSummary(department) {
  if (!department) {
    return {
      intro: '暂无科室简介',
      morningCount: 0,
      afternoonCount: 0,
    }
  }

  const bios = []
  let morningCount = 0
  let afternoonCount = 0

  department.doctors.forEach((doctor) => {
    const bio = doctor.bio?.trim()
    if (bio && !bios.includes(bio)) {
      bios.push(bio)
    }

    ;(doctor.timeSlots || []).forEach((slot) => {
      const [start = ''] = slot.split('-')
      const hour = Number(start.split(':')[0])
      if (Number.isNaN(hour)) return
      if (hour < 12) morningCount += 1
      else afternoonCount += 1
    })
  })

  return {
    intro: bios.length > 0 ? bios.join('；').slice(0, 56) : '暂无科室简介',
    morningCount,
    afternoonCount,
  }
}
```

- [ ] **Step 2: 在组件内部基于 `activeDepartment` 生成摘要**

```jsx
const departmentSummary = useMemo(
  () => buildDepartmentSummary(activeDepartment),
  [activeDepartment]
)
```

- [ ] **Step 3: 把当前科室块替换为摘要卡结构**

```jsx
<div className="schedule-current-dept">
  <div className="schedule-current-dept-label">当前科室</div>
  <div className="schedule-current-dept-name">{activeDepartment.departmentName}</div>
  <p className="schedule-current-dept-intro">{departmentSummary.intro}</p>
  <div className="schedule-current-dept-stats">
    <div className="schedule-current-dept-stat">
      <span className="schedule-current-dept-stat-label">上午号源</span>
      <span className="schedule-current-dept-stat-value">{departmentSummary.morningCount}</span>
    </div>
    <div className="schedule-current-dept-stat">
      <span className="schedule-current-dept-stat-label">下午号源</span>
      <span className="schedule-current-dept-stat-value">{departmentSummary.afternoonCount}</span>
    </div>
  </div>
</div>
```

- [ ] **Step 4: 运行单测确认当前科室摘要卡断言通过**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: PASS 或仅剩样式相关断言未通过。

- [ ] **Step 5: 提交摘要推导逻辑**

```bash
git add patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx
git commit -m "feat: add current department summary data"
```

### Task 3: 给当前科室摘要卡补样式并保持排班模块内部可滚动

**Files:**
- Modify: `patient_agent_frontend/src/index.css`
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: `.schedule-workbench-panel`, `.schedule-current-dept`
- Produces: 当前科室摘要卡样式与排班模块内部滚动约束

- [ ] **Step 1: 为当前科室摘要卡增加轻量样式**

```css
.schedule-current-dept {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: #F8FBFD;
  flex-shrink: 0;
}

.schedule-current-dept-intro {
  margin-top: 8px;
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}

.schedule-current-dept-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
```

- [ ] **Step 2: 为上午/下午号源块补数值层级**

```css
.schedule-current-dept-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
}

.schedule-current-dept-stat-label {
  font-size: 11px;
  color: #64748B;
}

.schedule-current-dept-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #0F172A;
}
```

- [ ] **Step 3: 收紧测试，继续锁定排班模块内部滚动能力**

```jsx
expect(appStyles).toMatch(/\.schedule-workbench-panel\s*\{[^}]*flex:\s*1;/)
expect(appStyles).toMatch(/\.schedule-list\s*\{[^}]*overflow-y:\s*auto;/)
expect(appStyles).toMatch(/\.schedule-current-dept\s*\{[^}]*flex-shrink:\s*0;/)
```

- [ ] **Step 4: 运行单测确认 UI 与样式断言全部通过**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: PASS，当前科室摘要卡展示和滚动样式断言全部通过。

- [ ] **Step 5: 提交摘要卡样式**

```bash
git add patient_agent_frontend/src/index.css patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx
git commit -m "feat: style current department summary card"
```

### Task 4: 完整验证当前科室摘要卡变更

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/index.css`
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`
- Modify: `patient_agent_frontend/src/mocks/scheduleData.js`

**Interfaces:**
- Consumes: 任务 1-3 的测试、推导逻辑与样式
- Produces: 通过验证的当前科室摘要卡功能

- [ ] **Step 1: 跑前端测试全集**

Run: `npm test`  
Expected: PASS，`patient_agent_frontend` 全部测试通过。

- [ ] **Step 2: 跑生产构建确认打包正常**

Run: `npm run build`  
Expected: PASS，Vite 构建成功。

- [ ] **Step 3: 检查关键文件改动范围是否聚焦**

Run: `git status --short -- patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx patient_agent_frontend/src/index.css patient_agent_frontend/src/mocks/scheduleData.js`  
Expected: 仅显示当前科室摘要卡相关文件变更。

- [ ] **Step 4: 如验证通过，准备交付说明**

```text
- 当前科室摘要卡显示科室简介
- 当前科室摘要卡显示上午/下午号源数量
- 简介缺失时显示“暂无科室简介”
- 医院排班模块在小高度下仍保持内部可滚动浏览
```

- [ ] **Step 5: 提交最终收口**

```bash
git add patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx patient_agent_frontend/src/index.css patient_agent_frontend/src/mocks/scheduleData.js
git commit -m "feat: add current department summary card"
```
