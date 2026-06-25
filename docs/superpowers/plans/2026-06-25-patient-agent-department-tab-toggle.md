# Patient Agent Department Tab Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为医院排班模块增加“当前已选科室再次点击可取消选择”的交互，并在取消后显示空状态提示。

**Architecture:** 保持 `expandedDeptIndex` 作为唯一的科室选中状态源，不新增额外状态字段。先用测试锁定“默认选中、再次点击取消、空状态展示、再次点击恢复、弹窗关闭”的行为，再在 `HospitalScheduleCard` 里补最小切换逻辑。

**Tech Stack:** React 19、Vite 8、Vitest、Testing Library

## Global Constraints

- 页面初始加载后仍自动选中第一个有排班的科室。
- 如果用户点击的是当前未选中的科室，则正常切换。
- 如果用户点击的是当前已选中的科室，则取消选择。
- 取消选择后，显示医院排班空状态提示。
- 不新增额外图标、复选标记或“清空选择”按钮。
- 当前科室摘要卡展示规则不变。
- 上午 / 下午号源统计逻辑不变。
- 若取消选择前已打开挂号确认弹窗，取消后弹窗同步关闭。

---

### Task 1: 锁定科室 tab 二次点击取消选择的失败测试

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: `HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading })`
- Produces: “二次点击取消 + 空状态 + 再次恢复 + 弹窗关闭”的回归测试

- [ ] **Step 1: 新增一条失败测试，覆盖再次点击当前科室后取消选择**

```jsx
it('deselects the current department when clicking the selected tab again', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={[
        {
          departmentId: 'dept-1',
          departmentName: '心血管内科',
          doctors: [
            {
              doctorId: 'doctor-1',
              doctorName: '王主任',
              title: '主任医师',
              bio: '擅长冠心病与高血压诊疗',
              timeSlots: ['08:00-12:00'],
            },
          ],
        },
        {
          departmentId: 'dept-2',
          departmentName: '神经内科',
          doctors: [
            {
              doctorId: 'doctor-2',
              doctorName: '赵医生',
              title: '副主任医师',
              bio: '擅长头痛与眩晕管理',
              timeSlots: ['14:00-17:30'],
            },
          ],
        },
      ]}
    />
  )

  const cardioTab = screen.getByRole('tab', { name: /心血管内科/ })
  expect(cardioTab).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByText('王主任')).toBeInTheDocument()

  fireEvent.click(cardioTab)

  expect(cardioTab).toHaveAttribute('aria-selected', 'false')
  expect(screen.queryByText('王主任')).not.toBeInTheDocument()
  expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()
})
```

- [ ] **Step 2: 新增一条失败测试，覆盖取消后再次点击任意科室可恢复**

```jsx
it('restores the department content after reselecting a tab from empty state', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={[
        {
          departmentId: 'dept-1',
          departmentName: '心血管内科',
          doctors: [
            {
              doctorId: 'doctor-1',
              doctorName: '王主任',
              title: '主任医师',
              bio: '擅长冠心病与高血压诊疗',
              timeSlots: ['08:00-12:00'],
            },
          ],
        },
      ]}
    />
  )

  const cardioTab = screen.getByRole('tab', { name: /心血管内科/ })

  fireEvent.click(cardioTab)
  expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()

  fireEvent.click(cardioTab)

  expect(cardioTab).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByText('王主任')).toBeInTheDocument()
  expect(screen.queryByText('请选择科室查看今日排班')).not.toBeInTheDocument()
})
```

- [ ] **Step 3: 新增一条失败测试，覆盖取消选择时关闭挂号确认弹窗**

```jsx
it('closes the confirm modal when deselecting the current department', () => {
  render(
    <HospitalScheduleCard
      user={{ name: '张三' }}
      onSendChat={vi.fn()}
      dateLabel="2026年6月25日 周四"
      loading={false}
      departments={[
        {
          departmentId: 'dept-1',
          departmentName: '心血管内科',
          doctors: [
            {
              doctorId: 'doctor-1',
              doctorName: '王主任',
              title: '主任医师',
              bio: '擅长冠心病与高血压诊疗',
              timeSlots: ['08:00-12:00'],
            },
          ],
        },
      ]}
    />
  )

  fireEvent.click(screen.getByRole('button', { name: '预约挂号' }))
  expect(screen.getByText('确认挂号信息')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('tab', { name: /心血管内科/ }))

  expect(screen.queryByText('确认挂号信息')).not.toBeInTheDocument()
  expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()
})
```

- [ ] **Step 4: 运行局部测试确认它先失败**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: FAIL，原因是当前已选科室再次点击时仍保持选中，不会进入空状态。

- [ ] **Step 5: 提交测试基线**

```bash
git add patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx
git commit -m "test: cover department tab deselection"
```

### Task 2: 在 HospitalScheduleCard 中实现二次点击取消选择

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`

**Interfaces:**
- Consumes: `expandedDeptIndex: number | null`
- Produces: `handleDepartmentToggle(index: number): void`

- [ ] **Step 1: 在组件内部新增 tab 切换函数，统一处理切换与取消**

```jsx
const handleDepartmentToggle = (index) => {
  setExpandedDeptIndex((currentIndex) => (
    currentIndex === index ? null : index
  ))
}
```

- [ ] **Step 2: 用统一切换函数替换 tab 点击逻辑**

```jsx
<button
  key={department.departmentId}
  type="button"
  role="tab"
  aria-selected={isActive}
  className={`schedule-dept-nav-item ${isActive ? 'active' : ''}`}
  onClick={() => handleDepartmentToggle(index)}
>
```

- [ ] **Step 3: 保持空状态渲染分支不变，复用现有未选择提示**

```jsx
{activeDepartment ? (
  <div className="schedule-workbench-panel">
    {/* 当前科室摘要卡 + 医生列表 */}
  </div>
) : departments.length === 0 ? (
  <div className="schedule-placeholder">
    <Stethoscope size={30} className="placeholder-icon" />
    <p className="placeholder-text">当前暂无可展示排班</p>
  </div>
) : (
  <div className="schedule-placeholder">
    <Stethoscope size={30} className="placeholder-icon" />
    <p className="placeholder-text">请选择科室查看今日排班</p>
  </div>
)}
```

- [ ] **Step 4: 运行局部测试确认取消选择行为通过**

Run: `npm test -- src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: PASS，新增的取消选择、恢复显示、弹窗关闭断言全部通过。

- [ ] **Step 5: 提交交互实现**

```bash
git add patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx
git commit -m "feat: support department tab deselection"
```

### Task 3: 完整验证科室 tab 取消选择交互

**Files:**
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: 任务 1-2 的测试与组件逻辑
- Produces: 通过验证的二次点击取消选择交互

- [ ] **Step 1: 跑前端测试全集**

Run: `npm test`  
Expected: PASS，`patient_agent_frontend` 全部测试通过。

- [ ] **Step 2: 跑生产构建确认打包正常**

Run: `npm run build`  
Expected: PASS，Vite 构建成功。

- [ ] **Step 3: 检查改动范围是否聚焦**

Run: `git status --short -- patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`  
Expected: 仅显示本次交互变更相关文件。

- [ ] **Step 4: 准备交付说明**

```text
- 当前已选科室再次点击可取消选择
- 取消后显示“请选择科室查看今日排班”
- 再次点击任意科室可恢复摘要卡和医生列表
- 若取消前已打开挂号确认弹窗，取消后弹窗同步关闭
```

- [ ] **Step 5: 提交最终收口**

```bash
git add patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx
git commit -m "feat: add department tab toggle behavior"
```
