# Patient Agent Frontend E2E Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a frontend page-journey benchmark pack for `patient_agent_frontend`, including a human-readable e2e checklist and a machine-readable JSON dataset.

**Architecture:** Reuse the existing `benchmark/patient_agent` directory and keep the new artifacts aligned with the existing backend-capability benchmark. One Markdown file serves manual regression and review, while one JSON file serves future Playwright/Vitest/custom e2e runners.

**Tech Stack:** Markdown, JSON, existing React/Vitest codebase evidence, repository docs

## Global Constraints

- Only cover frontend page flows that already exist in `patient_agent_frontend`.
- Keep the benchmark style aligned with `benchmark/patient_agent/patient-agent-benchmark.json`.
- Include both positive assertions and forbidden behaviors for every case.
- Every case must reference evidence from existing implementation files or existing tests.
- Do not add Playwright code in this task.

---

### Task 1: Define Frontend E2E Dataset

**Files:**
- Create: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-frontend-e2e.json`
- Modify: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/README.md`
- Test: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-frontend-e2e.json`

**Interfaces:**
- Consumes: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-benchmark.json`
- Produces: A JSON dataset with top-level keys `benchmark_id`, `generated_on`, `based_on`, `journeys`, `cases`

- [ ] **Step 1: Write the target structure**

```json
{
  "benchmark_id": "patient-agent-frontend-e2e-v1",
  "generated_on": "2026-06-28",
  "based_on": [
    "benchmark/patient_agent/patient-agent-benchmark.json"
  ],
  "journeys": [],
  "cases": []
}
```

- [ ] **Step 2: Add journey definitions**

```json
{
  "id": "JOURNEY-001",
  "name": "登录进入聊天页",
  "pages": ["login_page", "chat_page"],
  "goal": "验证患者从登录页成功进入聊天页的完整入口链路"
}
```

- [ ] **Step 3: Add case definitions**

```json
{
  "id": "FE-E2E-001",
  "journey": "JOURNEY-001",
  "page": "login_page",
  "priority": "P0",
  "related_case_ids": ["AUTH-001", "AUTH-002"],
  "preconditions": ["页面初始处于未登录状态"],
  "steps": ["输入合法手机号", "点击获取验证码", "输入验证码", "点击登录"],
  "expected": ["进入聊天页", "显示聊天输入框"],
  "forbidden": ["登录成功后仍停留在登录页"],
  "evidence": {
    "frontend": ["patient_agent_frontend/src/App.jsx"],
    "tests": ["patient_agent_frontend/src/App.thread-context.test.jsx"]
  }
}
```

- [ ] **Step 4: Update benchmark README**

```md
- `patient-agent-frontend-e2e.json`
  - 前端页面操作流 benchmark 数据
  - 用于手工页面回归和后续 Playwright/Vitest e2e 接入
```

- [ ] **Step 5: Verify JSON parses**

Run: `python3 - <<'PY'
import json
from pathlib import Path
p = Path('/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-frontend-e2e.json')
json.loads(p.read_text())
print('json ok')
PY`

Expected: PASS and print `json ok`

### Task 2: Write Human-Readable E2E Checklist

**Files:**
- Create: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/frontend-e2e-cases.md`
- Test: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/frontend-e2e-cases.md`

**Interfaces:**
- Consumes: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-frontend-e2e.json`
- Produces: A Markdown checklist grouped by journey with manual regression steps

- [ ] **Step 1: Add document header and scope**

```md
# patient_agent 前端页面操作流 E2E Case 清单

本清单用于人工回归和后续 Playwright 场景映射。
```

- [ ] **Step 2: Group cases by journey**

```md
## Journey 1: 登录进入聊天页

- Case ID: `FE-E2E-001`
- 页面：`login_page` -> `chat_page`
- 前置条件：未登录
- 操作步骤：
  1. 输入手机号
  2. 获取验证码
  3. 输入验证码
  4. 点击登录
```

- [ ] **Step 3: Include assertions and failure signals**

```md
- 期望结果：
  - 进入聊天页
  - 出现聊天输入框
- 失败信号：
  - 停留在登录页
  - 无 toast 或无状态变化
```

- [ ] **Step 4: Include related benchmark links**

```md
- 关联基线 case：`AUTH-001`、`AUTH-002`
```

- [ ] **Step 5: Review for consistency with JSON**

Run: `python3 - <<'PY'
from pathlib import Path
text = Path('/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/frontend-e2e-cases.md').read_text()
assert 'FE-E2E-001' in text
print('markdown ok')
PY`

Expected: PASS and print `markdown ok`

### Task 3: Verify Coverage and Handoff

**Files:**
- Modify: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/README.md`
- Test: `/Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/README.md`

**Interfaces:**
- Consumes: Newly created Markdown and JSON artifacts
- Produces: Updated benchmark index and final verification evidence

- [ ] **Step 1: Add the new files to the README structure section**

```md
- `frontend-e2e-cases.md`
  - 前端页面旅程型 e2e 回归清单
- `patient-agent-frontend-e2e.json`
  - 前端页面旅程型 e2e 机器可读数据
```

- [ ] **Step 2: Add recommended usage**

```md
### 4. 作为前端页面回归入口

- 先跑登录和线程恢复旅程
- 再跑聊天和侧栏挂号旅程
- 最后跑线程删除成功/失败分支
```

- [ ] **Step 3: Run full verification**

Run: `python3 - <<'PY'
import json
from pathlib import Path
root = Path('/Users/bytedance/Desktop/mywork/Smart-healthcar-system')
json_path = root / 'benchmark/patient_agent/patient-agent-frontend-e2e.json'
md_path = root / 'benchmark/patient_agent/frontend-e2e-cases.md'
readme = root / 'benchmark/patient_agent/README.md'
data = json.loads(json_path.read_text())
assert len(data['journeys']) >= 8
assert len(data['cases']) >= 10
assert md_path.exists()
assert readme.exists()
print('frontend e2e benchmark ok')
PY`

Expected: PASS and print `frontend e2e benchmark ok`

- [ ] **Step 4: Commit**

```bash
git add \
  /Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/frontend-e2e-cases.md \
  /Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/patient-agent-frontend-e2e.json \
  /Users/bytedance/Desktop/mywork/Smart-healthcar-system/benchmark/patient_agent/README.md \
  /Users/bytedance/Desktop/mywork/Smart-healthcar-system/docs/superpowers/specs/2026-06-28-patient-agent-frontend-e2e-benchmark-design.md \
  /Users/bytedance/Desktop/mywork/Smart-healthcar-system/docs/superpowers/plans/2026-06-28-patient-agent-frontend-e2e-benchmark.md
git commit -m "docs: add patient agent frontend e2e benchmark"
```
