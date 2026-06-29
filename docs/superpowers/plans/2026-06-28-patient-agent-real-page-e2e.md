# Patient Agent Real Page E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build real browser E2E coverage for `patient_agent` using Playwright on the host machine against frontend and backend services running in local Docker containers.

**Architecture:** Add a deterministic backend E2E mode that serves fixed auth/thread/sidebar/SSE data without browser-layer mocking, expose reset/status control APIs for Playwright, then run Playwright from the host against Docker-exposed frontend and backend ports via a unified Docker orchestration script. Keep benchmark JSON as the requirements source and map each Playwright test title to `FE-E2E-*` case ids.

**Tech Stack:** FastAPI, Pydantic Settings, Redis/MySQL-aware backend wiring, Docker Compose, Playwright, Node.js, Vite, Bash

## Global Constraints

- 浏览器执行真实页面
- 本地真实前端，且运行在本机 Docker 中
- 本地真实后端，且运行在本机 Docker 中
- 页面请求走 Docker 中运行的本地真实后端，而不是浏览器层 mock
- Playwright 建议运行在宿主机，而不是放进前端容器内部
- 首版只要求本地 Chromium 通过，不扩展到 Firefox 或 WebKit
- 首版页面级 E2E 直接映射 `benchmark/patient_agent/patient-agent-frontend-e2e.json` 中已定义的旅程与 case
- 固定主回归账号为 `13800138000 / 123456 / patient_id=12 / 张三`
- 失败时必须输出页面截图、trace 和服务日志

## File Map

- Create: `patient_agent_backend/app/e2e/__init__.py`
- Create: `patient_agent_backend/app/e2e/fixtures.py`
- Create: `patient_agent_backend/app/e2e/service.py`
- Create: `patient_agent_backend/app/api/e2e.py`
- Modify: `patient_agent_backend/app/config/settings.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_backend/app/api/auth.py`
- Modify: `patient_agent_backend/app/api/chat.py`
- Modify: `patient_agent_backend/app/api/patient.py`
- Create: `patient_agent_backend/tests/test_e2e/test_service.py`
- Create: `patient_agent_backend/tests/test_api/test_e2e_api.py`
- Create: `docker-compose.patient-agent-e2e.yml`
- Create: `scripts/patient-agent-e2e.sh`
- Modify: `patient_agent_frontend/package.json`
- Create: `patient_agent_frontend/playwright.config.js`
- Create: `patient_agent_frontend/e2e/utils/e2eApi.js`
- Create: `patient_agent_frontend/e2e/fixtures/appHarness.js`
- Create: `patient_agent_frontend/e2e/smoke.spec.js`
- Create: `patient_agent_frontend/e2e/auth-login.spec.js`
- Create: `patient_agent_frontend/e2e/thread-recovery.spec.js`
- Create: `patient_agent_frontend/e2e/sidebar-registration.spec.js`
- Create: `patient_agent_frontend/e2e/thread-delete.spec.js`
- Modify: `benchmark/patient_agent/README.md`

---

### Task 1: Add Backend E2E Mode Foundation

**Files:**
- Create: `patient_agent_backend/app/e2e/__init__.py`
- Create: `patient_agent_backend/app/e2e/fixtures.py`
- Create: `patient_agent_backend/app/e2e/service.py`
- Modify: `patient_agent_backend/app/config/settings.py`
- Modify: `patient_agent_backend/tests/test_config/test_settings.py`
- Create: `patient_agent_backend/tests/test_e2e/test_service.py`

**Interfaces:**
- Produces: `Settings.patient_agent_e2e_mode: bool`
- Produces: `Settings.patient_agent_e2e_phone: str`
- Produces: `Settings.patient_agent_e2e_code: str`
- Produces: `Settings.patient_agent_e2e_patient_id: int`
- Produces: `Settings.patient_agent_e2e_patient_name: str`
- Produces: `get_e2e_service() -> PatientAgentE2EService`
- Produces: `PatientAgentE2EService.reset(scenario: str = "baseline") -> dict[str, object]`
- Produces: `PatientAgentE2EService.status() -> dict[str, object]`
- Produces: `PatientAgentE2EService.get_sms_code(phone: str) -> str`
- Produces: `PatientAgentE2EService.get_patient_identity(phone: str) -> dict[str, object]`

- [ ] **Step 1: Write the failing settings and service tests**

```python
# patient_agent_backend/tests/test_config/test_settings.py
def test_settings_parse_patient_agent_e2e_flags(monkeypatch):
    monkeypatch.setenv("PATIENT_AGENT_E2E_MODE", "true")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PHONE", "13800138000")
    monkeypatch.setenv("PATIENT_AGENT_E2E_CODE", "123456")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PATIENT_ID", "12")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PATIENT_NAME", "张三")

    settings = Settings()

    assert settings.patient_agent_e2e_mode is True
    assert settings.patient_agent_e2e_phone == "13800138000"
    assert settings.patient_agent_e2e_code == "123456"
    assert settings.patient_agent_e2e_patient_id == 12
    assert settings.patient_agent_e2e_patient_name == "张三"
```

```python
# patient_agent_backend/tests/test_e2e/test_service.py
from app.e2e.service import PatientAgentE2EService


def test_e2e_service_reset_restores_baseline_state():
    service = PatientAgentE2EService(
        phone="13800138000",
        code="123456",
        patient_id=12,
        patient_name="张三",
    )

    payload = service.reset("baseline")

    assert payload["scenario"] == "baseline"
    assert payload["patient"]["patient_id"] == 12
    assert payload["patient"]["phone"] == "13800138000"


def test_e2e_service_exposes_delete_failure_scenario():
    service = PatientAgentE2EService(
        phone="13800138000",
        code="123456",
        patient_id=12,
        patient_name="张三",
    )

    payload = service.reset("delete_thread_failure")

    assert payload["scenario"] == "delete_thread_failure"
    assert payload["delete_thread_should_fail"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./.venv-py312/bin/pytest patient_agent_backend/tests/test_config/test_settings.py patient_agent_backend/tests/test_e2e/test_service.py -q`

Expected: FAIL with missing `patient_agent_e2e_*` settings or `ModuleNotFoundError: No module named 'app.e2e'`

- [ ] **Step 3: Write the minimal backend E2E settings and fixture service**

```python
# patient_agent_backend/app/config/settings.py
class Settings(BaseSettings):
    ...
    patient_agent_e2e_mode: bool = False
    patient_agent_e2e_phone: str = "13800138000"
    patient_agent_e2e_code: str = "123456"
    patient_agent_e2e_patient_id: int = 12
    patient_agent_e2e_patient_name: str = "张三"
```

```python
# patient_agent_backend/app/e2e/fixtures.py
BASELINE_THREADS = [
    {
        "thread_id": "thread-1",
        "title": "历史对话一",
        "last_message": "这是历史消息",
        "updated_at": "2026-06-27T14:00:00",
    }
]

BASELINE_HISTORY = {
    "thread-1": [
        {"role": "user", "content": "这是历史消息"},
        {"role": "assistant", "content": "继续为您处理。"},
    ]
}

BASELINE_SIDEBAR = {
    "profile": {
        "id": 12,
        "name": "张三",
        "gender": "男",
        "age": 32,
        "recentVisits": [],
    },
    "recentVisits": [],
    "schedule": {
        "dateLabel": "2026-06-28",
        "departments": [
            {
                "departmentName": "心内科",
                "doctors": [
                    {"doctorId": 3, "doctorName": "张医生", "workPlanId": 11}
                ],
            }
        ],
    },
}
```

```python
# patient_agent_backend/app/e2e/service.py
from copy import deepcopy

from app.e2e.fixtures import BASELINE_HISTORY, BASELINE_SIDEBAR, BASELINE_THREADS


class PatientAgentE2EService:
    def __init__(self, *, phone: str, code: str, patient_id: int, patient_name: str):
        self.phone = phone
        self.code = code
        self.patient_id = patient_id
        self.patient_name = patient_name
        self._scenario = "baseline"
        self._state = {}
        self.reset()

    def reset(self, scenario: str = "baseline") -> dict[str, object]:
        self._scenario = scenario
        self._state = {
            "threads": deepcopy(BASELINE_THREADS),
            "history": deepcopy(BASELINE_HISTORY),
            "sidebar": deepcopy(BASELINE_SIDEBAR),
            "delete_thread_should_fail": scenario == "delete_thread_failure",
            "sidebar_should_fail": scenario == "sidebar_load_failure",
        }
        return self.status()

    def status(self) -> dict[str, object]:
        return {
            "enabled": True,
            "scenario": self._scenario,
            "patient": {
                "phone": self.phone,
                "patient_id": self.patient_id,
                "name": self.patient_name,
            },
            "delete_thread_should_fail": self._state["delete_thread_should_fail"],
            "sidebar_should_fail": self._state["sidebar_should_fail"],
        }

    def get_sms_code(self, phone: str) -> str:
        if phone != self.phone:
            raise ValueError("unsupported e2e phone")
        return self.code

    def get_patient_identity(self, phone: str) -> dict[str, object]:
        if phone != self.phone:
            raise ValueError("unsupported e2e phone")
        return {
            "token": "e2e-token-1",
            "patient_id": self.patient_id,
            "name": self.patient_name,
            "phone": self.phone,
        }


_service: PatientAgentE2EService | None = None


def get_e2e_service() -> PatientAgentE2EService:
    global _service
    from app.config.settings import settings

    if _service is None:
        _service = PatientAgentE2EService(
            phone=settings.patient_agent_e2e_phone,
            code=settings.patient_agent_e2e_code,
            patient_id=settings.patient_agent_e2e_patient_id,
            patient_name=settings.patient_agent_e2e_patient_name,
        )
    return _service
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `./.venv-py312/bin/pytest patient_agent_backend/tests/test_config/test_settings.py patient_agent_backend/tests/test_e2e/test_service.py -q`

Expected: PASS with the new settings assertions and `2 passed` from `test_service.py`

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/config/settings.py \
  patient_agent_backend/app/e2e/__init__.py \
  patient_agent_backend/app/e2e/fixtures.py \
  patient_agent_backend/app/e2e/service.py \
  patient_agent_backend/tests/test_config/test_settings.py \
  patient_agent_backend/tests/test_e2e/test_service.py
git commit -m "feat: add patient agent e2e mode foundation"
```

### Task 2: Wire Deterministic Backend APIs And E2E Control Endpoints

**Files:**
- Create: `patient_agent_backend/app/api/e2e.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_backend/app/api/auth.py`
- Modify: `patient_agent_backend/app/api/chat.py`
- Modify: `patient_agent_backend/app/api/patient.py`
- Create: `patient_agent_backend/tests/test_api/test_e2e_api.py`

**Interfaces:**
- Consumes: `get_e2e_service() -> PatientAgentE2EService`
- Produces: `POST /api/e2e/reset` with body `{"scenario": "baseline" | "sidebar_load_failure" | "delete_thread_failure"}`
- Produces: `GET /api/e2e/status`
- Produces: auth E2E response `{"msg": "验证码已发送", "code_dev": "123456"}`
- Produces: login E2E response `{"token": "e2e-token-1", "patient_id": 12, "name": "张三"}`
- Produces: threads/history/sidebar/sidebar-action/chat-stream deterministic payloads for Playwright

- [ ] **Step 1: Write the failing API tests for reset/status and deterministic auth/chat flows**

```python
# patient_agent_backend/tests/test_api/test_e2e_api.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_e2e_reset_returns_selected_scenario(monkeypatch):
    monkeypatch.setenv("PATIENT_AGENT_E2E_MODE", "true")

    response = client.post("/api/e2e/reset", json={"scenario": "delete_thread_failure"})

    assert response.status_code == 200
    assert response.json()["scenario"] == "delete_thread_failure"
    assert response.json()["delete_thread_should_fail"] is True


def test_send_sms_returns_fixed_e2e_code(monkeypatch):
    monkeypatch.setenv("PATIENT_AGENT_E2E_MODE", "true")

    response = client.post("/api/auth/send-sms", json={"phone": "13800138000"})

    assert response.status_code == 200
    assert response.json()["code_dev"] == "123456"


def test_chat_threads_returns_e2e_thread_list(monkeypatch):
    monkeypatch.setenv("PATIENT_AGENT_E2E_MODE", "true")

    login = client.post("/api/auth/login", json={"phone": "13800138000", "code": "123456"})
    token = login.json()["token"]
    response = client.get("/api/chat/threads", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["threads"][0]["thread_id"] == "thread-1"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./.venv-py312/bin/pytest patient_agent_backend/tests/test_api/test_e2e_api.py -q`

Expected: FAIL with `404 Not Found` for `/api/e2e/reset` and random auth/chat behavior mismatches

- [ ] **Step 3: Implement the E2E control router and deterministic API branches**

```python
# patient_agent_backend/app/api/e2e.py
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.config.settings import settings
from app.e2e.service import get_e2e_service

router = APIRouter(prefix="/api/e2e", tags=["E2E"])


class ResetRequest(BaseModel):
    scenario: str = "baseline"


@router.get("/status")
async def status():
    if not settings.patient_agent_e2e_mode:
        raise HTTPException(status_code=404, detail="E2E mode disabled")
    return get_e2e_service().status()


@router.post("/reset")
async def reset(payload: ResetRequest):
    if not settings.patient_agent_e2e_mode:
        raise HTTPException(status_code=404, detail="E2E mode disabled")
    return get_e2e_service().reset(payload.scenario)
```

```python
# patient_agent_backend/app/api/auth.py
from app.config.settings import settings
from app.e2e.service import get_e2e_service

...

@router.post("/send-sms", response_model=SmsCodeResponse)
async def send_sms_code(request: SmsCodeRequest):
    if settings.patient_agent_e2e_mode:
        return SmsCodeResponse(msg="验证码已发送", code_dev=get_e2e_service().get_sms_code(request.phone))
    ...


@router.post("/login", response_model=PatientLoginResponse)
async def login(request: PatientLoginRequest):
    if settings.patient_agent_e2e_mode:
        identity = get_e2e_service().get_patient_identity(request.phone)
        if request.code != settings.patient_agent_e2e_code:
            raise HTTPException(status_code=400, detail="验证码错误")
        return PatientLoginResponse(
            token=identity["token"],
            patient_id=identity["patient_id"],
            name=identity["name"],
        )
    ...
```

```python
# patient_agent_backend/app/api/chat.py
from app.config.settings import settings
from app.e2e.service import get_e2e_service

...

@router.get("/threads")
async def chat_threads(session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return {"threads": get_e2e_service().list_threads(session.patient_id)}
    ...


@router.get("/history")
async def chat_history(thread_id: str = "", session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return {"messages": get_e2e_service().get_history(session.patient_id, thread_id), "thread_id": thread_id}
    ...


@router.post("/stream")
async def chat_stream(request: Request, session: PatientSession = Depends(require_patient_session)):
    ...
    if settings.patient_agent_e2e_mode:
        async def event_generator():
            for event in get_e2e_service().build_stream_events(
                patient_id=session.patient_id,
                user_message=user_message,
                thread_id=thread_id,
            ):
                yield {"event": event["event"], "data": json.dumps(event["data"], ensure_ascii=False)}
        return EventSourceResponse(event_generator())
```

```python
# patient_agent_backend/app/api/patient.py
from app.config.settings import settings
from app.e2e.service import get_e2e_service

...

@router.get("/sidebar")
async def get_sidebar(session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return get_e2e_service().get_sidebar(session.patient_id)
    ...


@router.post("/sidebar/action")
async def sidebar_action(payload: SidebarActionRequest, session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return get_e2e_service().run_sidebar_action(
            patient_id=session.patient_id,
            action=payload.action,
            thread_id=payload.thread_id,
            payload=payload.payload.model_dump() if hasattr(payload.payload, "model_dump") else payload.payload,
        )
    ...
```

```python
# patient_agent_backend/app/main.py
from app.api.e2e import router as e2e_router

...
app.include_router(e2e_router)
```

- [ ] **Step 4: Run the backend API tests to verify they pass**

Run: `./.venv-py312/bin/pytest patient_agent_backend/tests/test_api/test_e2e_api.py patient_agent_backend/tests/test_api/test_auth_api.py patient_agent_backend/tests/test_api/test_chat_stream_api.py -q`

Expected: PASS with deterministic `/api/e2e/*`, fixed auth code, and stable stream events

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/api/e2e.py \
  patient_agent_backend/app/main.py \
  patient_agent_backend/app/api/auth.py \
  patient_agent_backend/app/api/chat.py \
  patient_agent_backend/app/api/patient.py \
  patient_agent_backend/tests/test_api/test_e2e_api.py
git commit -m "feat: add deterministic patient agent e2e backend routes"
```

### Task 3: Add Host-Side Playwright And Docker Smoke Runner

**Files:**
- Create: `docker-compose.patient-agent-e2e.yml`
- Create: `scripts/patient-agent-e2e.sh`
- Modify: `patient_agent_frontend/package.json`
- Create: `patient_agent_frontend/playwright.config.js`
- Create: `patient_agent_frontend/e2e/utils/e2eApi.js`
- Create: `patient_agent_frontend/e2e/fixtures/appHarness.js`
- Create: `patient_agent_frontend/e2e/smoke.spec.js`

**Interfaces:**
- Consumes: `POST http://127.0.0.1:8001/api/e2e/reset`
- Produces: npm script `e2e`
- Produces: npm script `e2e:headed`
- Produces: shell entrypoint `scripts/patient-agent-e2e.sh`
- Produces: helper `resetE2EState(scenario?: string): Promise<void>`
- Produces: helper `loginAsDefaultPatient(page: Page): Promise<void>`

- [ ] **Step 1: Write the failing smoke spec**

```javascript
// patient_agent_frontend/e2e/smoke.spec.js
import { test, expect } from '@playwright/test'

test('FE-E2E-SMOKE login page is reachable from host browser', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible()
  await expect(page.getByRole('button', { name: '获取验证码' })).toBeVisible()
})
```

- [ ] **Step 2: Run the smoke spec to verify it fails before Playwright and Docker wiring exists**

Run: `cd patient_agent_frontend && npx playwright test e2e/smoke.spec.js`

Expected: FAIL with missing `@playwright/test`, missing config, or no reachable frontend service

- [ ] **Step 3: Add Docker override, Playwright config, host runner, and reset helpers**

```yaml
# docker-compose.patient-agent-e2e.yml
services:
  patient_agent_backend:
    environment:
      PATIENT_AGENT_E2E_MODE: "true"
      CORS_ALLOWED_ORIGINS: "http://127.0.0.1:5174,http://localhost:5174"
      OPENAI_API_KEY: "e2e-not-used"
  patient_agent_frontend:
    environment:
      VITE_API_BASE: http://patient_agent_backend:8000
```

```bash
# scripts/patient-agent-e2e.sh
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_ARGS=(-f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.patient-agent-e2e.yml")

cleanup() {
  docker compose "${COMPOSE_ARGS[@]}" logs patient_agent_backend patient_agent_frontend > "$ROOT/patient-agent-e2e.log" || true
  docker compose "${COMPOSE_ARGS[@]}" down || true
}

trap cleanup EXIT

docker compose "${COMPOSE_ARGS[@]}" up -d patient_agent_backend patient_agent_frontend
until curl -fsS http://127.0.0.1:8001/health >/dev/null; do sleep 2; done
until curl -fsS http://127.0.0.1:5174 >/dev/null; do sleep 2; done

cd "$ROOT/patient_agent_frontend"
npx playwright test "$@"
```

```javascript
// patient_agent_frontend/playwright.config.js
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 0,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://127.0.0.1:5174',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
```

```javascript
// patient_agent_frontend/e2e/utils/e2eApi.js
export async function resetE2EState(scenario = 'baseline') {
  const response = await fetch('http://127.0.0.1:8001/api/e2e/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  })
  if (!response.ok) {
    throw new Error(`reset failed: ${response.status}`)
  }
}
```

```javascript
// patient_agent_frontend/e2e/fixtures/appHarness.js
import { expect } from '@playwright/test'
import { resetE2EState } from '../utils/e2eApi'

export async function openLoginPage(page, scenario = 'baseline') {
  await resetE2EState(scenario)
  await page.context().clearCookies()
  await page.goto('/')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible()
}

export async function loginAsDefaultPatient(page) {
  await page.getByPlaceholder('请输入手机号').fill('13800138000')
  await page.getByRole('button', { name: '获取验证码' }).click()
  await page.getByPlaceholder('请输入验证码').fill('123456')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
}
```

```json
// patient_agent_frontend/package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "e2e": "playwright test",
    "e2e:headed": "playwright test --headed"
  },
  "devDependencies": {
    "@playwright/test": "^1.54.0",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.0",
    "@tailwindcss/vite": "^4.3.0",
    "@vitejs/plugin-react": "^6.0.2",
    "jsdom": "^27.0.1",
    "tailwindcss": "^4.3.0",
    "vite": "^8.0.14",
    "vitest": "^3.2.4"
  }
}
```

- [ ] **Step 4: Install Playwright and run the smoke spec to verify it passes**

Run: `cd patient_agent_frontend && PATH='/Users/bytedance/Library/Application Support/TRAE SOLO CN/ModularData/ai-agent/vm/tools/opt/node/26.3.0/bin':$PATH '/Users/bytedance/Library/Application Support/TRAE SOLO CN/ModularData/ai-agent/vm/tools/opt/node/26.3.0/bin/npm' install`

Expected: PASS with `added @playwright/test`

Run: `PATH='/Users/bytedance/Library/Application Support/TRAE SOLO CN/ModularData/ai-agent/vm/tools/opt/node/26.3.0/bin':$PATH '/Users/bytedance/Library/Application Support/TRAE SOLO CN/ModularData/ai-agent/vm/tools/opt/node/26.3.0/bin/npm' exec playwright install chromium`

Expected: PASS with Chromium installed locally

Run: `bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/smoke.spec.js`

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add docker-compose.patient-agent-e2e.yml \
  scripts/patient-agent-e2e.sh \
  patient_agent_frontend/package.json \
  patient_agent_frontend/package-lock.json \
  patient_agent_frontend/playwright.config.js \
  patient_agent_frontend/e2e/utils/e2eApi.js \
  patient_agent_frontend/e2e/fixtures/appHarness.js \
  patient_agent_frontend/e2e/smoke.spec.js
git commit -m "feat: add patient agent docker playwright smoke runner"
```

### Task 4: Implement Auth And Thread Journey Specs

**Files:**
- Create: `patient_agent_frontend/e2e/auth-login.spec.js`
- Create: `patient_agent_frontend/e2e/thread-recovery.spec.js`
- Modify: `patient_agent_frontend/e2e/fixtures/appHarness.js`

**Interfaces:**
- Consumes: `openLoginPage(page, scenario?: string): Promise<void>`
- Consumes: `loginAsDefaultPatient(page): Promise<void>`
- Produces: Playwright tests for `FE-E2E-001`, `FE-E2E-002`, `FE-E2E-003`, `FE-E2E-004`, `FE-E2E-005`

- [ ] **Step 1: Write the failing auth and thread recovery specs**

```javascript
// patient_agent_frontend/e2e/auth-login.spec.js
import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-001 登录成功进入聊天页', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
})

test('FE-E2E-002 非法手机号不触发登录', async ({ page }) => {
  await openLoginPage(page)
  await page.getByPlaceholder('请输入手机号').fill('123')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByText('请输入正确的手机号码')).toBeVisible()
})

test('FE-E2E-003 空验证码不触发登录', async ({ page }) => {
  await openLoginPage(page)
  await page.getByPlaceholder('请输入手机号').fill('13800138000')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByText('请输入验证码')).toBeVisible()
})
```

```javascript
// patient_agent_frontend/e2e/thread-recovery.spec.js
import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-004 历史线程恢复并展示', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await expect(page.getByText('历史对话一')).toBeVisible()
})

test('FE-E2E-005 页面刷新后继续在原线程续聊', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.getByText('历史对话一').click()
  await page.reload()
  await page.getByPlaceholder('描述您的症状或健康问题...').fill('继续刚才的话题')
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText('继续为您处理。')).toBeVisible()
})
```

- [ ] **Step 2: Run the specs to verify they fail before helper refinements**

Run: `bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/auth-login.spec.js patient_agent_frontend/e2e/thread-recovery.spec.js`

Expected: FAIL with at least one missing reset/login/thread assertion mismatch

- [ ] **Step 3: Refine the Playwright harness for login state, storage inspection, and thread waits**

```javascript
// patient_agent_frontend/e2e/fixtures/appHarness.js
import { expect } from '@playwright/test'
import { resetE2EState } from '../utils/e2eApi'

export async function openLoginPage(page, scenario = 'baseline') {
  await resetE2EState(scenario)
  await page.context().clearCookies()
  await page.goto('/')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible()
}

export async function loginAsDefaultPatient(page) {
  await page.getByPlaceholder('请输入手机号').fill('13800138000')
  await page.getByRole('button', { name: '获取验证码' }).click()
  await expect(page.getByText(/验证码已发送/)).toBeVisible()
  await page.getByPlaceholder('请输入验证码').fill('123456')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
}

export async function readCurrentSession(page) {
  return page.evaluate(() => JSON.parse(localStorage.getItem('patient_current_session') || 'null'))
}

export async function waitForThreadVisible(page, title) {
  await expect(page.getByText(title)).toBeVisible()
}
```

- [ ] **Step 4: Run the auth and thread specs to verify they pass**

Run: `bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/auth-login.spec.js patient_agent_frontend/e2e/thread-recovery.spec.js`

Expected: PASS with `5 passed`

- [ ] **Step 5: Commit**

```bash
git add patient_agent_frontend/e2e/auth-login.spec.js \
  patient_agent_frontend/e2e/thread-recovery.spec.js \
  patient_agent_frontend/e2e/fixtures/appHarness.js
git commit -m "feat: add patient agent auth and thread e2e journeys"
```

### Task 5: Implement Sidebar/Delete Journeys, Documentation, And Full Verification

**Files:**
- Create: `patient_agent_frontend/e2e/sidebar-registration.spec.js`
- Create: `patient_agent_frontend/e2e/thread-delete.spec.js`
- Modify: `benchmark/patient_agent/README.md`

**Interfaces:**
- Consumes: `openLoginPage(page, scenario?: string): Promise<void>`
- Consumes: `loginAsDefaultPatient(page): Promise<void>`
- Produces: Playwright tests for `FE-E2E-006`, `FE-E2E-008`, `FE-E2E-009`, `FE-E2E-010`, `FE-E2E-011`
- Produces: benchmark README run instructions for Docker + Playwright E2E

- [ ] **Step 1: Write the failing sidebar and delete journey specs**

```javascript
// patient_agent_frontend/e2e/sidebar-registration.spec.js
import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-006 右侧栏失败时展示 fallback', async ({ page }) => {
  await openLoginPage(page, 'sidebar_load_failure')
  await loginAsDefaultPatient(page)
  await expect(page.getByText('张三')).toBeVisible()
  await expect(page.getByText('心内科')).toBeVisible()
})

test('FE-E2E-008 右侧栏确认挂号', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.getByRole('button', { name: '预约挂号' }).click()
  await expect(page.getByText('确认挂号信息')).toBeVisible()
  await page.getByRole('button', { name: '确认挂号' }).click()
  await expect(page.getByText('已为您确认挂号。')).toBeVisible()
})

test('FE-E2E-009 侧栏动作切换服务端线程后继续聊天', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.getByRole('button', { name: '预约挂号' }).click()
  await page.getByRole('button', { name: '确认挂号' }).click()
  await page.getByPlaceholder('描述您的症状或健康问题...').fill('继续处理刚才那次挂号')
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText('继续处理完成。')).toBeVisible()
})
```

```javascript
// patient_agent_frontend/e2e/thread-delete.spec.js
import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-010 删除线程成功', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.getByTitle('删除对话').click()
  await page.getByRole('button', { name: '删除' }).click()
  await expect(page.getByText('历史对话一')).toHaveCount(0)
})

test('FE-E2E-011 删除线程失败时回滚本地列表', async ({ page }) => {
  await openLoginPage(page, 'delete_thread_failure')
  await loginAsDefaultPatient(page)
  await page.getByTitle('删除对话').click()
  await page.getByRole('button', { name: '删除' }).click()
  await expect(page.getByText('删除失败，请稍后重试')).toBeVisible()
  await expect(page.getByText('历史对话一')).toBeVisible()
})
```

- [ ] **Step 2: Run the specs to verify they fail before the backend scenarios and selectors are fully aligned**

Run: `bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/sidebar-registration.spec.js patient_agent_frontend/e2e/thread-delete.spec.js`

Expected: FAIL with at least one modal/sidebar/delete scenario mismatch

- [ ] **Step 3: Implement the final Playwright assertions and benchmark execution docs**

```markdown
<!-- benchmark/patient_agent/README.md -->
## 5. 作为真实页面级 E2E 回归入口

宿主机执行 Playwright，前后端运行在本机 Docker 中：

    bash scripts/patient-agent-e2e.sh

如需只跑单个 spec：

    bash scripts/patient-agent-e2e.sh patient_agent_frontend/e2e/thread-delete.spec.js
```

```javascript
// patient_agent_frontend/e2e/sidebar-registration.spec.js
test('FE-E2E-008 右侧栏确认挂号', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.getByRole('button', { name: '预约挂号' }).click()
  await expect(page.getByText('确认挂号信息')).toBeVisible()
  await page.getByRole('button', { name: '确认挂号' }).click()
  await expect(page.getByText('已为您确认挂号。')).toBeVisible()
  await expect(page.getByText('确认挂号：心内科 · 张医生')).toBeVisible()
})
```

```javascript
// patient_agent_frontend/e2e/thread-delete.spec.js
test('FE-E2E-011 删除线程失败时回滚本地列表', async ({ page }) => {
  await openLoginPage(page, 'delete_thread_failure')
  await loginAsDefaultPatient(page)
  await page.getByTitle('删除对话').click()
  await page.getByRole('button', { name: '删除' }).click()
  await expect(page.getByText('删除失败，请稍后重试')).toBeVisible()
  await expect(page.getByText('历史对话一')).toBeVisible()
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
})
```

- [ ] **Step 4: Run full verification**

Run: `./.venv-py312/bin/pytest patient_agent_backend/tests/test_config/test_settings.py patient_agent_backend/tests/test_e2e/test_service.py patient_agent_backend/tests/test_api/test_e2e_api.py -q`

Expected: PASS with backend E2E support tests all green

Run: `bash scripts/patient-agent-e2e.sh`

Expected: PASS with smoke, auth-login, thread-recovery, sidebar-registration, and thread-delete specs all green under Chromium

- [ ] **Step 5: Commit**

```bash
git add patient_agent_frontend/e2e/sidebar-registration.spec.js \
  patient_agent_frontend/e2e/thread-delete.spec.js \
  benchmark/patient_agent/README.md
git commit -m "feat: add patient agent real page e2e journeys"
```

## Self-Review

- Spec coverage:
  - Docker topology: covered in Task 3 via `docker-compose.patient-agent-e2e.yml` and `scripts/patient-agent-e2e.sh`
  - Backend E2E mode/reset/status: covered in Tasks 1-2
  - Host-side Playwright against Docker-exposed ports: covered in Task 3
  - Journey mapping to benchmark: covered in Tasks 4-5
  - Reports/screenshots/trace: covered in Task 3 Playwright config and Task 5 verification
- Placeholder scan:
  - No unresolved placeholders remain
- Type consistency:
  - `get_e2e_service()`, `resetE2EState()`, `openLoginPage()`, and `loginAsDefaultPatient()` are defined before later tasks consume them
