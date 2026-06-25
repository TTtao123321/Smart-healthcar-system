# Patient Agent Auth Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `patient_agent_backend` 成为唯一患者认证入口，返回真实 `patient_user_info.id`，新增患者档案接口，并打通 Agent 端患者挂号链路。

**Architecture:** `patient_agent_backend` 保留短信验证码登录入口，但把患者主数据改为直连 HMS MySQL 的 `patient_user_info`，并用 Redis 保存 Agent 自有登录态。聊天、SSE、挂号工具统一从 Bearer token 解析患者身份；`hospital_manage_backend` 删除患者认证链路并补齐 `POST /medical_registration/save` 业务接口。

**Tech Stack:** FastAPI、Redis、`aiomysql`、Pydantic、React + Axios、Spring Boot、MyBatis XML、Sa-Token、JUnit 5、Mockito

## Global Constraints

- 患者登录只走 `patient_agent_backend /api/auth/*`
- 患者真实身份统一为 `patient_user_info.id`
- 后端不信任前端传入的 `patient_id`
- `chat`、`chat/stream`、`chat/history`、`logout` 必须要求已登录
- HMS 只删除患者认证代码，不影响管理端 `/user/login` 和后台权限体系
- `POST /medical_registration/save` 必须在当前仓库真实落地，不能只保留 Agent 侧调用
- 若前端仍传 `patient_id`，后端首期兼容接收但必须忽略

---

## File Map

- `patient_agent_backend/app/config/settings.py`
  - 增加 HMS MySQL 连接配置
- `patient_agent_backend/pyproject.toml`
  - 增加 `aiomysql` 依赖
- `patient_agent_backend/app/patient_profile/models.py`
  - 患者档案读写模型
- `patient_agent_backend/app/patient_profile/repository.py`
  - 访问 `patient_user_info`
- `patient_agent_backend/app/patient_profile/service.py`
  - 查询、自动建档、更新档案
- `patient_agent_backend/app/auth/models.py`
  - 登录态与认证上下文模型
- `patient_agent_backend/app/auth/service.py`
  - token 创建、读取、失效
- `patient_agent_backend/app/auth/dependencies.py`
  - FastAPI 认证依赖
- `patient_agent_backend/app/api/auth.py`
  - 登录/登出改造为真实患者身份
- `patient_agent_backend/app/api/patient.py`
  - 新增患者档案查询与更新接口
- `patient_agent_backend/app/api/chat.py`
  - 接入认证依赖，去掉前端透传患者身份
- `patient_agent_backend/app/agent/request_context.py`
  - 存储认证态患者上下文
- `patient_agent_backend/app/main.py`
  - 初始化 MySQL 连接池并注册患者档案路由
- `patient_agent_backend/app/tools/registration_tools.py`
  - 挂号工具统一从认证上下文取真实患者 ID
- `patient_agent_backend/tests/test_patient_profile/test_service.py`
  - 患者档案服务测试
- `patient_agent_backend/tests/test_api/test_auth_api.py`
  - 登录/登出接口测试
- `patient_agent_backend/tests/test_api/test_chat_auth.py`
  - 聊天鉴权测试
- `patient_agent_backend/tests/test_api/test_patient_profile_api.py`
  - 患者档案接口测试
- `patient_agent_backend/tests/test_tools/test_registration_tools_auth.py`
  - 挂号工具认证上下文测试
- `patient_agent_frontend/src/api/index.js`
  - 新增患者档案 API，聊天请求不再传 `patient_id`
- `patient_agent_frontend/src/App.jsx`
  - 登录后保存真实 `patient_id`，聊天页改用 token 身份
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/MedicalRegistrationController.java`
  - 新增挂号创建接口
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertMedicalRegistrationForm.java`
  - 创建挂号表单
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/pojo/MedicalRegistration.java`
  - 挂号实体
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/MedicalRegistrationDao.java`
  - 挂号 DAO
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/MedicalRegistrationService.java`
  - 挂号服务接口
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java`
  - 挂号服务实现
- `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml`
  - 挂号 SQL
- `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java`
  - 挂号服务测试
- `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/MedicalRegistrationControllerTest.java`
  - 挂号控制器测试
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientPortalAuthService.java`
  - 删除
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientPortalAuthServiceImpl.java`
  - 删除
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/satoken/StpPatientUtil.java`
  - 删除
- `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/config/StpPatientConfig.java`
  - 删除

### Task 1: Add Patient Profile Data Layer

**Files:**
- Create: `patient_agent_backend/app/patient_profile/models.py`
- Create: `patient_agent_backend/app/patient_profile/repository.py`
- Create: `patient_agent_backend/app/patient_profile/service.py`
- Modify: `patient_agent_backend/app/config/settings.py`
- Modify: `patient_agent_backend/pyproject.toml`
- Modify: `patient_agent_backend/app/main.py`
- Test: `patient_agent_backend/tests/test_patient_profile/test_service.py`

**Interfaces:**
- Consumes: `settings` from `app/config/settings.py`
- Produces: `PatientProfile`, `PatientProfileUpdate`, `PatientProfileService.get_or_create_by_phone(phone: str) -> PatientProfile`, `PatientProfileService.get_by_id(patient_id: int) -> PatientProfile | None`, `PatientProfileService.update_profile(patient_id: int, payload: PatientProfileUpdate) -> PatientProfile`

- [ ] **Step 1: Write the failing patient profile service tests**

```python
from app.patient_profile.models import PatientProfile, PatientProfileUpdate
from app.patient_profile.service import PatientProfileService


class FakeRepository:
    def __init__(self):
        self.by_phone = {}
        self.by_id = {}

    async def get_by_phone(self, phone: str):
        return self.by_phone.get(phone)

    async def get_by_id(self, patient_id: int):
        return self.by_id.get(patient_id)

    async def create_patient(self, profile: PatientProfile):
        self.by_phone[profile.tel] = profile
        self.by_id[profile.id] = profile
        return profile

    async def update_patient_basic_info(self, patient_id: int, payload: PatientProfileUpdate):
        current = self.by_id[patient_id]
        updated = current.model_copy(update=payload.model_dump(exclude_unset=True))
        self.by_id[patient_id] = updated
        self.by_phone[updated.tel] = updated
        return updated


async def test_get_or_create_by_phone_creates_new_patient():
    repo = FakeRepository()
    service = PatientProfileService(repo)

    profile = await service.get_or_create_by_phone("13800138000")

    assert profile.id > 0
    assert profile.tel == "13800138000"
    assert profile.name == "患者8000"


async def test_update_profile_updates_allowed_fields_only():
    repo = FakeRepository()
    repo.by_id[7] = PatientProfile(id=7, uuid="u7", name="患者8000", tel="13800138000")
    service = PatientProfileService(repo)

    updated = await service.update_profile(7, PatientProfileUpdate(name="张三", sex="男"))

    assert updated.id == 7
    assert updated.tel == "13800138000"
    assert updated.name == "张三"
```

- [ ] **Step 2: Run the patient profile tests and confirm they fail**

Run: `pytest patient_agent_backend/tests/test_patient_profile/test_service.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.patient_profile'`

- [ ] **Step 3: Add MySQL config and `aiomysql` dependency**

```python
# patient_agent_backend/app/config/settings.py
class Settings(BaseSettings):
    ...
    hms_db_host: str = "127.0.0.1"
    hms_db_port: int = 3306
    hms_db_name: str = "hospital"
    hms_db_user: str = "root"
    hms_db_password: str = ""
```

```toml
# patient_agent_backend/pyproject.toml
dependencies = [
    ...
    "aiomysql>=0.2.0",
]
```

- [ ] **Step 4: Implement patient profile models and service**

```python
# patient_agent_backend/app/patient_profile/models.py
from pydantic import BaseModel, ConfigDict


class PatientProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    name: str
    sex: str | None = None
    pid: str | None = None
    tel: str
    birthday: str | None = None
    insurance_type: int | None = None
    medical_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None


class PatientProfileUpdate(BaseModel):
    name: str | None = None
    sex: str | None = None
    pid: str | None = None
    birthday: str | None = None
    insurance_type: int | None = None
    medical_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None
```

```python
# patient_agent_backend/app/patient_profile/service.py
import uuid

from app.patient_profile.models import PatientProfile, PatientProfileUpdate


class PatientProfileService:
    def __init__(self, repository):
        self._repository = repository

    async def get_or_create_by_phone(self, phone: str) -> PatientProfile:
        profile = await self._repository.get_by_phone(phone)
        if profile:
            return profile
        created = PatientProfile(
            id=0,
            uuid=uuid.uuid4().hex,
            name=f"患者{phone[-4:]}",
            tel=phone,
        )
        return await self._repository.create_patient(created)

    async def get_by_id(self, patient_id: int) -> PatientProfile | None:
        return await self._repository.get_by_id(patient_id)

    async def update_profile(self, patient_id: int, payload: PatientProfileUpdate) -> PatientProfile:
        return await self._repository.update_patient_basic_info(patient_id, payload)
```

- [ ] **Step 5: Implement repository and app startup wiring**

```python
# patient_agent_backend/app/patient_profile/repository.py
class PatientProfileRepository:
    def __init__(self, pool):
        self._pool = pool

    async def get_by_phone(self, phone: str):
        sql = """
        SELECT id, uuid, name, sex, pid, tel, birthday,
               insurance_type, medical_history, allergy_history, family_history
        FROM patient_user_info
        WHERE tel=%s
        LIMIT 1
        """
        ...

    async def create_patient(self, profile):
        sql = """
        INSERT INTO patient_user_info(uuid, name, sex, pid, tel, birthday, password,
                                      medical_history, allergy_history, family_history, insurance_type)
        VALUES(%s, %s, %s, %s, %s, %s, '', %s, %s, %s, %s)
        """
        ...
```

```python
# patient_agent_backend/app/main.py
import aiomysql

...
pool = await aiomysql.create_pool(
    host=settings.hms_db_host,
    port=settings.hms_db_port,
    user=settings.hms_db_user,
    password=settings.hms_db_password,
    db=settings.hms_db_name,
    autocommit=True,
)
app.state.mysql_pool = pool
```

- [ ] **Step 6: Run the patient profile tests again**

Run: `pytest patient_agent_backend/tests/test_patient_profile/test_service.py -q`

Expected: PASS with `2 passed`

- [ ] **Step 7: Commit**

```bash
git add patient_agent_backend/app/config/settings.py \
  patient_agent_backend/pyproject.toml \
  patient_agent_backend/app/main.py \
  patient_agent_backend/app/patient_profile \
  patient_agent_backend/tests/test_patient_profile/test_service.py
git commit -m "feat: add patient profile data layer"
```

### Task 2: Refactor Patient Auth To Use Real HMS Patient IDs

**Files:**
- Create: `patient_agent_backend/app/auth/models.py`
- Create: `patient_agent_backend/app/auth/service.py`
- Modify: `patient_agent_backend/app/api/auth.py`
- Modify: `patient_agent_backend/app/main.py`
- Test: `patient_agent_backend/tests/test_api/test_auth_api.py`

**Interfaces:**
- Consumes: `PatientProfileService.get_or_create_by_phone(phone: str) -> PatientProfile`
- Produces: `PatientSession`, `AuthService.create_session(phone: str, name: str, patient_id: int) -> PatientSession`, `AuthService.get_session(token: str) -> PatientSession | None`, `AuthService.logout(token: str) -> None`

- [ ] **Step 1: Write the failing auth API tests**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_login_returns_real_patient_id(monkeypatch):
    client = TestClient(app)

    async def fake_login(phone: str, code: str):
        return {"token": "token-1", "patient_id": 12, "name": "张三"}

    monkeypatch.setattr("app.api.auth.login_with_code", fake_login)

    response = client.post("/api/auth/login", json={"phone": "13800138000", "code": "123456"})

    assert response.status_code == 200
    assert response.json()["patient_id"] == 12


def test_logout_requires_bearer_token(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 401
```

- [ ] **Step 2: Run the auth API tests and confirm they fail**

Run: `pytest patient_agent_backend/tests/test_api/test_auth_api.py -q`

Expected: FAIL because `login_with_code` does not exist and `logout` does not enforce authentication

- [ ] **Step 3: Add auth models and service**

```python
# patient_agent_backend/app/auth/models.py
from pydantic import BaseModel


class PatientSession(BaseModel):
    token: str
    patient_id: int
    phone: str
    name: str
    login_time: str
```

```python
# patient_agent_backend/app/auth/service.py
import uuid
from datetime import datetime

from app.auth.models import PatientSession


class AuthService:
    def __init__(self, redis_client):
        self._redis = redis_client

    async def create_session(self, phone: str, name: str, patient_id: int) -> PatientSession:
        token = str(uuid.uuid4())
        session = PatientSession(
            token=token,
            patient_id=patient_id,
            phone=phone,
            name=name,
            login_time=datetime.now().isoformat(),
        )
        await self._redis.hset(f"patient:token:{token}", mapping=session.model_dump())
        await self._redis.expire(f"patient:token:{token}", 86400 * 7)
        return session
```

- [ ] **Step 4: Refactor `/api/auth/login` and `/api/auth/logout`**

```python
# patient_agent_backend/app/api/auth.py
async def login(request: PatientLoginRequest):
    ...
    profile_service = get_patient_profile_service()
    auth_service = get_auth_service()
    profile = await profile_service.get_or_create_by_phone(request.phone)
    session = await auth_service.create_session(
        phone=request.phone,
        name=profile.name,
        patient_id=profile.id,
    )
    return PatientLoginResponse(
        token=session.token,
        patient_id=session.patient_id,
        name=session.name,
    )


@router.post("/logout")
async def logout(session: PatientSession = Depends(require_patient_session)):
    await get_auth_service().logout(session.token)
    return {"msg": "登出成功"}
```

- [ ] **Step 5: Run the auth API tests again**

Run: `pytest patient_agent_backend/tests/test_api/test_auth_api.py -q`

Expected: PASS with `2 passed`

- [ ] **Step 6: Commit**

```bash
git add patient_agent_backend/app/auth \
  patient_agent_backend/app/api/auth.py \
  patient_agent_backend/app/main.py \
  patient_agent_backend/tests/test_api/test_auth_api.py
git commit -m "feat: bind patient auth to hms patient ids"
```

### Task 3: Enforce Auth On Chat And Request Context

**Files:**
- Modify: `patient_agent_backend/app/auth/dependencies.py`
- Modify: `patient_agent_backend/app/api/chat.py`
- Modify: `patient_agent_backend/app/agent/request_context.py`
- Test: `patient_agent_backend/tests/test_api/test_chat_auth.py`

**Interfaces:**
- Consumes: `AuthService.get_session(token: str) -> PatientSession | None`
- Produces: `require_patient_session() -> PatientSession`, `set_patient_session(session: PatientSession | None) -> None`, `get_patient_id() -> int | None`

- [ ] **Step 1: Write the failing chat auth tests**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_chat_requires_login():
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "我要挂号"})
    assert response.status_code == 401


def test_chat_ignores_forwarded_patient_id(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(
        "app.auth.dependencies.require_patient_session",
        lambda: {"token": "t", "patient_id": 88, "name": "张三", "phone": "13800138000"},
    )
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer t"},
        json={"message": "你好", "patient_id": 999},
    )
    assert response.status_code != 500
```

- [ ] **Step 2: Run the chat auth tests and confirm they fail**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_auth.py -q`

Expected: FAIL because `/api/chat` still accepts anonymous traffic and still reads `patient_id` from request body

- [ ] **Step 3: Add auth dependency and patient session context**

```python
# patient_agent_backend/app/auth/dependencies.py
from fastapi import Header, HTTPException


async def require_patient_session(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.removeprefix("Bearer ").strip()
    session = await get_auth_service().get_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session
```

```python
# patient_agent_backend/app/agent/request_context.py
from contextvars import ContextVar

from app.auth.models import PatientSession

current_patient_session: ContextVar[PatientSession | None] = ContextVar("current_patient_session", default=None)


def set_patient_session(session: PatientSession | None) -> None:
    current_patient_session.set(session)


def get_patient_id() -> int | None:
    session = current_patient_session.get()
    return session.patient_id if session else None
```

- [ ] **Step 4: Refactor chat endpoints to use authenticated patient identity**

```python
# patient_agent_backend/app/api/chat.py
@router.post("")
async def chat(request: Request, session: PatientSession = Depends(require_patient_session)):
    body = await request.json()
    user_message = body.get("message", "")
    patient_id = session.patient_id
    ...


@router.post("/stream")
async def chat_stream(request: Request, session: PatientSession = Depends(require_patient_session)):
    body = await request.json()
    user_message = body.get("message", "")
    patient_id = session.patient_id
    ...
    set_patient_session(session)
```

- [ ] **Step 5: Run the chat auth tests again**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_auth.py -q`

Expected: PASS with `2 passed`

- [ ] **Step 6: Commit**

```bash
git add patient_agent_backend/app/auth/dependencies.py \
  patient_agent_backend/app/api/chat.py \
  patient_agent_backend/app/agent/request_context.py \
  patient_agent_backend/tests/test_api/test_chat_auth.py
git commit -m "feat: require auth for patient chat endpoints"
```

### Task 4: Add Patient Profile APIs And Frontend Integration

**Files:**
- Create: `patient_agent_backend/app/api/patient.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/App.jsx`
- Test: `patient_agent_backend/tests/test_api/test_patient_profile_api.py`

**Interfaces:**
- Consumes: `require_patient_session() -> PatientSession`, `PatientProfileService.get_by_id()`, `PatientProfileService.update_profile()`
- Produces: `GET /api/patient/profile`, `POST /api/patient/profile`, `patientApi.getProfile()`, `patientApi.updateProfile(payload)`

- [ ] **Step 1: Write the failing patient profile API tests**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_get_profile_returns_current_patient_profile(client):
    response = client.get("/api/patient/profile", headers={"Authorization": "Bearer token-1"})
    assert response.status_code == 200
    assert response.json()["id"] == 12


def test_update_profile_does_not_allow_tel_change(client):
    response = client.post(
        "/api/patient/profile",
        headers={"Authorization": "Bearer token-1"},
        json={"name": "张三", "tel": "13900139000"},
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run the patient profile API tests and confirm they fail**

Run: `pytest patient_agent_backend/tests/test_api/test_patient_profile_api.py -q`

Expected: FAIL because `/api/patient/profile` does not exist

- [ ] **Step 3: Implement backend patient profile routes**

```python
# patient_agent_backend/app/api/patient.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/patient", tags=["患者档案"])


@router.get("/profile")
async def get_profile(session: PatientSession = Depends(require_patient_session)):
    profile = await get_patient_profile_service().get_by_id(session.patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    return profile.model_dump()


@router.post("/profile")
async def update_profile(payload: PatientProfileUpdate, session: PatientSession = Depends(require_patient_session)):
    profile = await get_patient_profile_service().update_profile(session.patient_id, payload)
    return profile.model_dump()
```

- [ ] **Step 4: Update frontend API layer and login/chat usage**

```javascript
// patient_agent_frontend/src/api/index.js
export const patientApi = {
  getProfile() {
    return api.get('/patient/profile')
  },
  updateProfile(payload) {
    return api.post('/patient/profile', payload)
  },
}

export const chatApi = {
  send(message, threadId) {
    return api.post('/chat', { message, thread_id: threadId })
  },
  sendStream(message, threadId) {
    return fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(localStorage.getItem('patient_token')
          ? { Authorization: `Bearer ${localStorage.getItem('patient_token')}` }
          : {}),
      },
      body: JSON.stringify({ message, thread_id: threadId }),
    })
  },
}
```

```javascript
// patient_agent_frontend/src/App.jsx
const { token, patient_id, name } = res.data
const userInfo = { name, token, patient_id, phone }
```

- [ ] **Step 5: Run backend API tests and frontend build verification**

Run: `pytest patient_agent_backend/tests/test_api/test_patient_profile_api.py -q`

Expected: PASS with `2 passed`

Run: `npm run build`

Expected: `vite build` completes successfully

- [ ] **Step 6: Commit**

```bash
git add patient_agent_backend/app/api/patient.py \
  patient_agent_backend/app/main.py \
  patient_agent_backend/tests/test_api/test_patient_profile_api.py \
  patient_agent_frontend/src/api/index.js \
  patient_agent_frontend/src/App.jsx
git commit -m "feat: add patient profile apis and frontend wiring"
```

### Task 5: Use Auth Context In Registration Tools

**Files:**
- Modify: `patient_agent_backend/app/tools/registration_tools.py`
- Modify: `patient_agent_backend/app/api/chat.py`
- Test: `patient_agent_backend/tests/test_tools/test_registration_tools_auth.py`

**Interfaces:**
- Consumes: `get_patient_id() -> int | None`, `RegistrationService.create(request: RegistrationCreateRequest) -> RegistrationCreateResponse`
- Produces: `resolve_patient_card_id(patient_card_id: int | None) -> int`, authenticated behavior for `create_registration`, `query_registration`, `cancel_registration`

- [ ] **Step 1: Write the failing registration tool auth tests**

```python
import pytest

from app.tools.registration_tools import create_registration_tools


@pytest.mark.asyncio
async def test_create_registration_requires_logged_in_patient(fake_hms_client):
    tools = create_registration_tools(fake_hms_client)
    create_registration = next(tool for tool in tools if tool.name == "create_registration")

    with pytest.raises(ValueError, match="请先登录"):
        await create_registration.ainvoke({
            "work_plan_id": 1,
            "doctor_schedule_id": 2,
            "doctor_id": 3,
            "dept_sub_id": 4,
            "appointment_date": "2026-06-25",
            "slot": 1,
        })
```

- [ ] **Step 2: Run the registration tool tests and confirm they fail**

Run: `pytest patient_agent_backend/tests/test_tools/test_registration_tools_auth.py -q`

Expected: FAIL because the tool still accepts missing auth context or forwarded patient IDs

- [ ] **Step 3: Refactor the patient ID resolver**

```python
# patient_agent_backend/app/tools/registration_tools.py
def resolve_patient_card_id(explicit_patient_card_id: int | None = None) -> int:
    if explicit_patient_card_id is not None:
        return explicit_patient_card_id
    patient_id = get_patient_id()
    if patient_id is None:
        raise ValueError("请先登录后再挂号")
    return patient_id
```

- [ ] **Step 4: Update the registration tools to rely on auth context**

```python
@tool
async def create_registration(..., patient_card_id: int | None = None) -> str:
    resolved_patient_id = resolve_patient_card_id(patient_card_id)
    request = RegistrationCreateRequest(
        patient_card_id=resolved_patient_id,
        work_plan_id=work_plan_id,
        doctor_schedule_id=doctor_schedule_id,
        doctor_id=doctor_id,
        dept_sub_id=dept_sub_id,
        appointment_date=appointment_date,
        slot=slot,
    )
    result = await hms_client.registration_service.create(request)
    return format_success(result)
```

- [ ] **Step 5: Run the registration tool tests again**

Run: `pytest patient_agent_backend/tests/test_tools/test_registration_tools_auth.py -q`

Expected: PASS with `1 passed`

- [ ] **Step 6: Commit**

```bash
git add patient_agent_backend/app/tools/registration_tools.py \
  patient_agent_backend/app/api/chat.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_auth.py
git commit -m "feat: bind registration tools to auth context"
```

### Task 6: Implement HMS Medical Registration Save API

**Files:**
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/MedicalRegistrationController.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertMedicalRegistrationForm.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/pojo/MedicalRegistration.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/MedicalRegistrationDao.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/MedicalRegistrationService.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/MedicalRegistrationControllerTest.java`

**Interfaces:**
- Consumes: `patient_user_info`, `medical_registration`, `doctor_work_plan_schedule`
- Produces: `MedicalRegistrationService.save(MedicalRegistration entity) -> int`, `POST /medical_registration/save`

- [ ] **Step 1: Write the failing HMS service and controller tests**

```java
@Test
@DisplayName("save_正常创建挂号并返回主键")
void save_正常创建挂号并返回主键() {
    InsertMedicalRegistrationForm form = new InsertMedicalRegistrationForm();
    form.setPatientCardId(1);
    form.setWorkPlanId(10);
    form.setDoctorScheduleId(100);
    form.setDoctorId(8);
    form.setDeptSubId(3);
    form.setDate("2026-06-25");
    form.setSlot(1);

    when(medicalRegistrationService.save(any(MedicalRegistration.class))).thenReturn(66);

    CommonResult result = controller.save(form);

    assertEquals(200, result.get("code"));
    assertEquals(66, ((Map<?, ?>) result.get("result")).get("id"));
}
```

```java
@Test
@DisplayName("save_号源已满时抛出异常")
void save_号源已满时抛出异常() {
    MedicalRegistration entity = new MedicalRegistration();
    entity.setDoctorScheduleId(100);

    when(scheduleDao.selectScheduleById(100)).thenReturn(Map.of("maximum", 10, "num", 10));

    assertThrows(GlobalException.class, () -> service.save(entity));
}
```

- [ ] **Step 2: Run the HMS tests and confirm they fail**

Run: `mvn -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest,MedicalRegistrationControllerTest test`

Expected: FAIL because the classes and endpoint do not exist

- [ ] **Step 3: Implement form, entity, DAO, mapper, and service**

```java
// InsertMedicalRegistrationForm.java
@Data
public class InsertMedicalRegistrationForm {
    @NotNull @Min(1)
    private Integer patientCardId;
    @NotNull @Min(1)
    private Integer workPlanId;
    @NotNull @Min(1)
    private Integer doctorScheduleId;
    @NotNull @Min(1)
    private Integer doctorId;
    @NotNull @Min(1)
    private Integer deptSubId;
    @NotBlank
    private String date;
    @NotNull @Range(min = 1, max = 15)
    private Integer slot;
}
```

```java
// MedicalRegistrationServiceImpl.java
@Transactional
public int save(MedicalRegistration entity) {
    HashMap<String, Object> patient = patientDao.selectPatientInfoById(entity.getPatientCardId());
    if (patient == null) {
        throw new GlobalException("患者不存在");
    }
    HashMap<String, Object> schedule = medicalRegistrationDao.selectScheduleById(entity.getDoctorScheduleId());
    if (schedule == null) {
        throw new GlobalException("排班不存在");
    }
    int maximum = MapUtil.getInt(schedule, "maximum");
    int num = MapUtil.getInt(schedule, "num");
    if (num >= maximum) {
        throw new GlobalException("当前号源已满");
    }
    medicalRegistrationDao.insert(entity);
    medicalRegistrationDao.increaseScheduleNum(entity.getDoctorScheduleId());
    return entity.getId();
}
```

```xml
<!-- MedicalRegistrationDao.xml -->
<insert id="insert" parameterType="com.hospital.hms.pojo.MedicalRegistration" useGeneratedKeys="true" keyProperty="id">
    INSERT INTO medical_registration
    (patient_card_id, work_plan_id, doctor_schedule_id, doctor_id, dept_sub_id, date, slot, status, payment_status)
    VALUES
    (#{patientCardId}, #{workPlanId}, #{doctorScheduleId}, #{doctorId}, #{deptSubId},
     STR_TO_DATE(#{date}, '%Y-%m-%d'), #{slot}, 0, 0)
</insert>
```

- [ ] **Step 4: Implement the controller**

```java
@RestController
@RequestMapping("/medical_registration")
@Tag(name = "MedicalRegistrationController", description = "挂号管理")
@Slf4j
public class MedicalRegistrationController {

    @Autowired
    private MedicalRegistrationService medicalRegistrationService;

    @PostMapping("/save")
    @Operation(summary = "创建挂号")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult save(@RequestBody @Valid InsertMedicalRegistrationForm form) {
        MedicalRegistration entity = new MedicalRegistration();
        BeanUtil.copyProperties(form, entity);
        int id = medicalRegistrationService.save(entity);
        return CommonResult.ok().put("result", Map.of("id", id, "status", 0));
    }
}
```

- [ ] **Step 5: Run the HMS tests again**

Run: `mvn -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest,MedicalRegistrationControllerTest test`

Expected: PASS with `BUILD SUCCESS`

- [ ] **Step 6: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/MedicalRegistrationController.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertMedicalRegistrationForm.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/pojo/MedicalRegistration.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/MedicalRegistrationDao.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/MedicalRegistrationService.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java \
  hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/MedicalRegistrationControllerTest.java
git commit -m "feat: add hms medical registration save api"
```

### Task 7: Remove HMS Patient Auth Chain And Verify End To End

**Files:**
- Delete: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientPortalAuthService.java`
- Delete: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientPortalAuthServiceImpl.java`
- Delete: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/satoken/StpPatientUtil.java`
- Delete: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/config/StpPatientConfig.java`
- Modify: `patient_agent_backend/app/hms_client/services/registration_service.py`
- Test: `patient_agent_backend/tests/test_api/test_auth_api.py`
- Test: `patient_agent_backend/tests/test_tools/test_registration_tools_auth.py`

**Interfaces:**
- Consumes: new HMS `POST /medical_registration/save`, existing `/patient/selectByPage`, `/patient/updateRegistrationStatus`
- Produces: final single-entry patient auth architecture and working end-to-end registration flow

- [ ] **Step 1: Write the failing integration smoke checklist**

```text
1. patient_agent 登录后返回真实 patient_id
2. GET /api/patient/profile 能返回当前患者档案
3. create_registration 能调用 HMS /medical_registration/save
4. query_registration 能查询到当前患者挂号
5. cancel_registration 能取消当前患者挂号
```

- [ ] **Step 2: Remove the HMS patient auth classes**

```bash
rm hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientPortalAuthService.java
rm hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientPortalAuthServiceImpl.java
rm hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/satoken/StpPatientUtil.java
rm hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/config/StpPatientConfig.java
```

- [ ] **Step 3: Point Agent registration calls at the now-real HMS save endpoint**

```python
# patient_agent_backend/app/hms_client/services/registration_service.py
data = await self._client.post(
    "/medical_registration/save",
    json=request.model_dump(mode="json"),
)
```

- [ ] **Step 4: Run focused regression tests**

Run: `pytest patient_agent_backend/tests/test_api/test_auth_api.py patient_agent_backend/tests/test_tools/test_registration_tools_auth.py -q`

Expected: PASS

Run: `mvn -pl hospital_hms_api -Dtest=PatientControllerTest,MedicalRegistrationServiceImplTest,MedicalRegistrationControllerTest test`

Expected: `BUILD SUCCESS`

- [ ] **Step 5: Run end-to-end smoke verification**

Run: `pytest patient_agent_backend/tests/test_api/test_chat_auth.py patient_agent_backend/tests/test_api/test_patient_profile_api.py -q`

Expected: PASS

Run: `npm run build`

Expected: `vite build` completes successfully

- [ ] **Step 6: Commit**

```bash
git add patient_agent_backend/app/hms_client/services/registration_service.py \
  patient_agent_backend/tests/test_api/test_auth_api.py \
  patient_agent_backend/tests/test_api/test_chat_auth.py \
  patient_agent_backend/tests/test_api/test_patient_profile_api.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_auth.py \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms
git commit -m "refactor: unify patient auth and registration flow"
```

## Self-Review

- **Spec coverage:** 任务 1-2 覆盖患者档案与登录，任务 3 覆盖聊天鉴权，任务 4 覆盖档案接口与前端接线，任务 5 覆盖挂号工具身份收口，任务 6 覆盖 HMS `/medical_registration/save`，任务 7 覆盖删除 HMS 患者认证链路与最终联调。
- **Placeholder scan:** 计划中没有 `TBD`、`TODO`、`implement later` 或 “类似 Task N” 的占位表述。
- **Type consistency:** `patient_id` 在所有任务中均表示 `patient_user_info.id`；`PatientSession`、`PatientProfileService`、`require_patient_session`、`MedicalRegistrationService.save` 的签名在前后任务中保持一致。
