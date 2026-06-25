# Patient Agent 右侧栏后端对接 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `patient_agent_frontend` 右侧栏接入真实后端数据，新增 `GET /api/patient/sidebar`，返回患者基础信息、最近 3 条就诊流水和当日医院排班。

**Architecture:** 在 `patient_agent_backend` 增加 `patient_sidebar` 聚合模块，复用当前登录患者身份、患者档案服务和 HMS client，统一输出前端右侧栏所需结构。前端只新增一条 `patientApi.getSidebar()` 请求，由 `PatientSidebar` 挂载时拉取真实数据并传给现有拆分组件，保留当前挂号确认后继续走 `onSendChat(...)` 的交互。

**Tech Stack:** Python FastAPI + Pydantic + pytest（后端），React 19 + Vite 8 + axios（前端）

## Global Constraints

- 仅通过 `patient_agent_backend` 暴露侧栏聚合接口，前端不直连 HMS
- 新增接口为 `GET /api/patient/sidebar`
- 必须要求患者已登录，从 Bearer token 解析真实 `patient_id`
- `profile` 查询失败时接口整体失败；`recentVisits` 和 `schedule` 查询失败时允许降级
- `recentVisits` 只返回最近 `3` 条真实挂号/就诊流水，按日期倒序
- `phone` 由后端脱敏，`idCardMasked` 只返回身份证后四位
- 前端不改变聊天主流程，不改变挂号确认后的 `onSendChat(...)`
- 前端当前没有测试框架，本次前端验证以 `vite build` 和联调核对为主，不额外引入 Vitest

---

### Task 1: 后端模型与适配器

**Files:**
- Create: `patient_agent_backend/app/patient_sidebar/__init__.py`
- Create: `patient_agent_backend/app/patient_sidebar/models.py`
- Create: `patient_agent_backend/app/patient_sidebar/adapters.py`
- Test: `patient_agent_backend/tests/test_patient_sidebar/test_adapters.py`

**Interfaces:**
- Consumes: `PatientProfile` from `app.patient_profile.models`; HMS payload dicts from `DoctorService` / `RegistrationService`
- Produces:
  - `SidebarProfile`
  - `SidebarRecentVisit`
  - `SidebarDoctor`
  - `SidebarDepartment`
  - `SidebarSchedule`
  - `SidebarResponse`
  - `build_sidebar_profile(profile: PatientProfile) -> SidebarProfile`
  - `build_recent_visits(items: list[dict], limit: int = 3) -> list[SidebarRecentVisit]`
  - `build_sidebar_schedule(date_str: str, departments: list[dict]) -> SidebarSchedule`

- [ ] **Step 1: 写 adapters 失败测试**

新建 `patient_agent_backend/tests/test_patient_sidebar/test_adapters.py`：

```python
from app.patient_profile.models import PatientProfile
from app.patient_sidebar.adapters import build_sidebar_profile, build_recent_visits


def test_build_sidebar_profile_masks_phone_and_pid():
    profile = PatientProfile(
        id=123,
        uuid="u1",
        name="张三",
        sex="男",
        pid="110101199001011234",
        tel="13812341024",
        birthday="1990-01-01",
        insurance_type=None,
        medical_history=None,
        allergy_history=None,
        family_history=None,
    )

    result = build_sidebar_profile(profile)

    assert result.patientId == "123"
    assert result.phone == "138****1024"
    assert result.idCardMasked == "1234"
    assert result.age is not None


def test_build_recent_visits_sorts_and_limits_items():
    items = [
        {"registrationId": 1, "date": "2026-06-01", "deptSubName": "内科门诊", "doctorName": "医生A"},
        {"registrationId": 2, "date": "2026-06-18", "deptSubName": "呼吸内科", "doctorName": "医生B"},
        {"registrationId": 3, "date": "2026-06-12", "deptSubName": "消化内科", "doctorName": "医生C"},
        {"registrationId": 4, "date": "2026-06-20", "deptSubName": "外科门诊", "doctorName": "医生D"},
    ]

    result = build_recent_visits(items, limit=3)

    assert [item.visitId for item in result] == ["4", "2", "3"]
    assert result[0].department == "外科门诊"
    assert len(result) == 3
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_patient_sidebar/test_adapters.py -q
```

Expected: FAIL，报 `ModuleNotFoundError: No module named 'app.patient_sidebar'` 或找不到适配函数。

- [ ] **Step 3: 实现 sidebar 模型与适配器**

新建 `patient_agent_backend/app/patient_sidebar/models.py`：

```python
from pydantic import BaseModel, Field


class SidebarProfile(BaseModel):
    patientId: str
    name: str
    gender: str | None = None
    age: int | None = None
    phone: str
    idCardMasked: str = ""


class SidebarRecentVisit(BaseModel):
    visitId: str
    visitDate: str
    department: str
    doctorName: str


class SidebarDoctor(BaseModel):
    doctorId: str
    doctorName: str
    title: str = ""
    bio: str = ""
    departmentName: str
    timeSlots: list[str] = Field(default_factory=list)


class SidebarDepartment(BaseModel):
    departmentId: str
    departmentName: str
    doctors: list[SidebarDoctor] = Field(default_factory=list)


class SidebarSchedule(BaseModel):
    dateLabel: str
    departments: list[SidebarDepartment] = Field(default_factory=list)


class SidebarResponse(BaseModel):
    profile: SidebarProfile
    recentVisits: list[SidebarRecentVisit] = Field(default_factory=list)
    schedule: SidebarSchedule
```

新建 `patient_agent_backend/app/patient_sidebar/adapters.py`：

```python
from datetime import date, datetime

from app.patient_profile.models import PatientProfile
from app.patient_sidebar.models import SidebarProfile, SidebarRecentVisit, SidebarSchedule, SidebarDepartment, SidebarDoctor


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_pid(pid: str | None) -> str:
    if not pid:
        return ""
    return pid[-4:]


def _calc_age(birthday: str | None) -> int | None:
    if not birthday:
        return None
    born = datetime.strptime(birthday, "%Y-%m-%d").date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def build_sidebar_profile(profile: PatientProfile) -> SidebarProfile:
    return SidebarProfile(
        patientId=str(profile.id),
        name=profile.name,
        gender=profile.sex,
        age=_calc_age(profile.birthday),
        phone=_mask_phone(profile.tel),
        idCardMasked=_mask_pid(profile.pid),
    )


def build_recent_visits(items: list[dict], limit: int = 3) -> list[SidebarRecentVisit]:
    normalized = []
    for item in items:
        visit_date = item.get("date") or ""
        normalized.append(
            SidebarRecentVisit(
                visitId=str(item.get("registrationId", item.get("id", ""))),
                visitDate=visit_date,
                department=item.get("deptSubName") or item.get("deptName") or "--",
                doctorName=item.get("doctorName") or "--",
            )
        )
    normalized.sort(key=lambda item: item.visitDate, reverse=True)
    return normalized[:limit]


def build_sidebar_schedule(date_str: str, departments: list[dict]) -> SidebarSchedule:
    sidebar_departments = []
    for department in departments:
        doctors = []
        for doctor in department.get("doctors", []):
            doctors.append(
                SidebarDoctor(
                    doctorId=str(doctor.get("doctorId", "")),
                    doctorName=doctor.get("doctorName", ""),
                    title=doctor.get("title", ""),
                    bio=doctor.get("bio", ""),
                    departmentName=department.get("departmentName", ""),
                    timeSlots=doctor.get("timeSlots", []),
                )
            )
        sidebar_departments.append(
            SidebarDepartment(
                departmentId=str(department.get("departmentId", "")),
                departmentName=department.get("departmentName", ""),
                doctors=doctors,
            )
        )
    return SidebarSchedule(dateLabel=date_str, departments=sidebar_departments)
```

并新建空文件 `patient_agent_backend/app/patient_sidebar/__init__.py`：

```python
__all__ = []
```

- [ ] **Step 4: 重新运行测试确认通过**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_patient_sidebar/test_adapters.py -q
```

Expected: PASS，2 个测试通过。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_backend/app/patient_sidebar/__init__.py \
  patient_agent_backend/app/patient_sidebar/models.py \
  patient_agent_backend/app/patient_sidebar/adapters.py \
  patient_agent_backend/tests/test_patient_sidebar/test_adapters.py && \
git commit -m "feat: add sidebar models and adapters"
```

### Task 2: 后端 service 聚合患者资料、最近就诊记录和医院排班

**Files:**
- Create: `patient_agent_backend/app/patient_sidebar/service.py`
- Modify: `patient_agent_backend/app/hms_client/services/registration_service.py`
- Test: `patient_agent_backend/tests/test_patient_sidebar/test_service.py`

**Interfaces:**
- Consumes:
  - `PatientProfileService.get_by_id(patient_id: int)`
  - `RegistrationService.query_recent(patient_card_id: int, limit: int = 3) -> list[dict]`
  - `SidebarProfile`, `SidebarSchedule`, `SidebarResponse`
- Produces:
  - `PatientSidebarService.get_sidebar(patient_id: int) -> SidebarResponse`
  - `RegistrationService.query_recent(...)`

- [ ] **Step 1: 写 service 失败测试**

新建 `patient_agent_backend/tests/test_patient_sidebar/test_service.py`：

```python
import pytest

from app.patient_profile.models import PatientProfile
from app.patient_sidebar.service import PatientSidebarService


class StubProfileService:
    async def get_by_id(self, patient_id: int):
        return PatientProfile(
            id=patient_id,
            uuid="u1",
            name="张三",
            sex="男",
            pid="110101199001011234",
            tel="13812341024",
            birthday="1990-01-01",
            insurance_type=None,
            medical_history=None,
            allergy_history=None,
            family_history=None,
        )


class StubRegistrationService:
    async def query_recent(self, patient_card_id: int, limit: int = 3):
        return [
            {"registrationId": 9, "date": "2026-06-18", "deptSubName": "呼吸内科", "doctorName": "李芳"},
        ]


class StubScheduleGateway:
    async def get_today_schedule(self):
        return {
            "dateLabel": "2026年6月24日 周三",
            "departments": [
                {
                    "departmentId": "1",
                    "departmentName": "内科",
                    "doctors": [
                        {
                            "doctorId": "2",
                            "doctorName": "张明华",
                            "title": "主任医师",
                            "bio": "擅长心血管疾病诊疗",
                            "timeSlots": ["08:00-12:00"],
                        }
                    ],
                }
            ],
        }


@pytest.mark.asyncio
async def test_get_sidebar_aggregates_profile_visits_and_schedule():
    service = PatientSidebarService(
        profile_service=StubProfileService(),
        registration_service=StubRegistrationService(),
        schedule_gateway=StubScheduleGateway(),
    )

    result = await service.get_sidebar(123)

    assert result.profile.patientId == "123"
    assert result.recentVisits[0].doctorName == "李芳"
    assert result.schedule.departments[0].departmentName == "内科"
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_patient_sidebar/test_service.py -q
```

Expected: FAIL，报 `ModuleNotFoundError` 或 `PatientSidebarService` 未定义。

- [ ] **Step 3: 为挂号服务补充最近就诊流水查询**

在 `patient_agent_backend/app/hms_client/services/registration_service.py` 中新增：

```python
    async def query_recent(self, patient_card_id: int, limit: int = 3) -> list[dict]:
        data = await self._client.post(
            "/patient/selectDetail",
            json={"patientCardId": patient_card_id},
        )

        result = data.get("result", {})
        registrations = result.get("registrations", [])
        registrations.sort(key=lambda item: item.get("date", ""), reverse=True)
        return registrations[:limit]
```

- [ ] **Step 4: 实现 sidebar 聚合 service**

新建 `patient_agent_backend/app/patient_sidebar/service.py`：

```python
from fastapi import HTTPException

from app.patient_sidebar.adapters import build_recent_visits, build_sidebar_profile, build_sidebar_schedule
from app.patient_sidebar.models import SidebarResponse


class PatientSidebarService:
    def __init__(self, profile_service, registration_service, schedule_gateway):
        self._profile_service = profile_service
        self._registration_service = registration_service
        self._schedule_gateway = schedule_gateway

    async def get_sidebar(self, patient_id: int) -> SidebarResponse:
        profile = await self._profile_service.get_by_id(patient_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="患者档案不存在")

        recent_visits = []
        try:
            visit_items = await self._registration_service.query_recent(patient_id, limit=3)
            recent_visits = build_recent_visits(visit_items, limit=3)
        except Exception:
            recent_visits = []

        schedule_payload = {"dateLabel": "", "departments": []}
        try:
            schedule_payload = await self._schedule_gateway.get_today_schedule()
        except Exception:
            schedule_payload = {"dateLabel": "", "departments": []}

        return SidebarResponse(
            profile=build_sidebar_profile(profile),
            recentVisits=recent_visits,
            schedule=build_sidebar_schedule(
                schedule_payload.get("dateLabel", ""),
                schedule_payload.get("departments", []),
            ),
        )
```

- [ ] **Step 5: 重新运行测试确认通过**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_patient_sidebar/test_service.py -q
```

Expected: PASS，聚合测试通过。

- [ ] **Step 6: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_backend/app/patient_sidebar/service.py \
  patient_agent_backend/app/hms_client/services/registration_service.py \
  patient_agent_backend/tests/test_patient_sidebar/test_service.py && \
git commit -m "feat: add patient sidebar aggregation service"
```

### Task 3: 后端接入排班聚合与 API 路由

**Files:**
- Create: `patient_agent_backend/app/patient_sidebar/schedule_gateway.py`
- Modify: `patient_agent_backend/app/api/patient.py`
- Modify: `patient_agent_backend/app/api/auth.py`
- Modify: `patient_agent_backend/app/hms_client/services/doctor_service.py`
- Test: `patient_agent_backend/tests/test_api/test_patient_sidebar_api.py`

**Interfaces:**
- Consumes:
  - `DoctorService.list_by_sub_dept(dept_sub_id: int) -> list[DoctorItem]`
  - `DoctorService.schedules(request: ScheduleListRequest) -> ScheduleListResponse`
  - `PatientSidebarService.get_sidebar(patient_id: int) -> SidebarResponse`
- Produces:
  - `PatientScheduleGateway.get_today_schedule() -> dict`
  - `GET /api/patient/sidebar`
  - `get_patient_sidebar_service()`

- [ ] **Step 1: 写 API 失败测试**

新建 `patient_agent_backend/tests/test_api/test_patient_sidebar_api.py`：

```python
from fastapi.testclient import TestClient

from app.main import app


def test_sidebar_requires_auth():
    client = TestClient(app)

    response = client.get("/api/patient/sidebar")

    assert response.status_code == 401


def test_sidebar_returns_aggregated_payload(monkeypatch):
    from app.api import patient as patient_api

    class StubSidebarService:
        async def get_sidebar(self, patient_id: int):
            return type(
                "SidebarResult",
                (),
                {
                    "model_dump": lambda self: {
                        "profile": {
                            "patientId": "123",
                            "name": "张三",
                            "gender": "男",
                            "age": 29,
                            "phone": "138****1024",
                            "idCardMasked": "1234",
                        },
                        "recentVisits": [],
                        "schedule": {"dateLabel": "2026年6月24日 周三", "departments": []},
                    }
                },
            )()

    monkeypatch.setattr(patient_api, "get_patient_sidebar_service", lambda: StubSidebarService())
    client = TestClient(app)
    token = "token"

    from app.auth.dependencies import set_auth_service_getter

    class StubAuthService:
        async def get_session(self, _token):
            return type("Session", (), {"patient_id": 123})()

    set_auth_service_getter(lambda: StubAuthService())

    response = client.get("/api/patient/sidebar", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["profile"]["patientId"] == "123"
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_patient_sidebar_api.py -q
```

Expected: FAIL，`/api/patient/sidebar` 不存在或 `get_patient_sidebar_service` 未定义。

- [ ] **Step 3: 实现排班聚合 gateway**

新建 `patient_agent_backend/app/patient_sidebar/schedule_gateway.py`：

```python
from datetime import date

from app.hms_client.models import ScheduleListRequest


def _slot_flags_to_labels(slot_flags: list[bool]) -> list[str]:
    labels = []
    if any(slot_flags[:8]):
        labels.append("08:00-12:00")
    if any(slot_flags[8:]):
        labels.append("14:00-17:30")
    return labels


class PatientScheduleGateway:
    def __init__(self, dept_service, doctor_service):
        self._dept_service = dept_service
        self._doctor_service = doctor_service

    async def get_today_schedule(self) -> dict:
        today = date.today()
        today_str = today.isoformat()
        date_label = f"{today.year}年{today.month}月{today.day}日"

        departments = []
        dept_items = await self._dept_service.list_all_names()
        for dept in dept_items:
            sub_depts = await self._dept_service.list_sub_depts(dept.id)
            doctors = []
            for sub_dept in sub_depts:
                doctor_items = await self._doctor_service.list_by_sub_dept(sub_dept.id)
                schedule_map = {}
                schedule_items = await self._doctor_service.schedules(
                    ScheduleListRequest(dept_sub_id=sub_dept.id, date=today_str)
                )
                for item in schedule_items.items:
                    schedule_map[item.get("doctorId")] = _slot_flags_to_labels(item.get("slot", []))

                for doctor in doctor_items:
                    slots = schedule_map.get(doctor.id, [])
                    if not slots:
                        continue
                    doctors.append(
                        {
                            "doctorId": str(doctor.id),
                            "doctorName": doctor.name,
                            "title": doctor.job or "",
                            "bio": doctor.description or "",
                            "timeSlots": slots,
                        }
                    )

            departments.append(
                {
                    "departmentId": str(dept.id),
                    "departmentName": dept.name,
                    "doctors": doctors,
                }
            )

        return {"dateLabel": date_label, "departments": departments}
```

- [ ] **Step 4: 暴露 sidebar service getter 并注册 API**

在 `patient_agent_backend/app/api/auth.py` 中添加：

```python
from app.patient_sidebar.service import PatientSidebarService
from app.patient_sidebar.schedule_gateway import PatientScheduleGateway
```

并在现有 getter 区域新增：

```python
_patient_sidebar_service = None


def get_patient_sidebar_service():
    global _patient_sidebar_service
    if _patient_sidebar_service is None:
        schedule_gateway = PatientScheduleGateway(
            get_hms_client().dept_service,
            get_hms_client().doctor_service,
        )
        _patient_sidebar_service = PatientSidebarService(
            profile_service=get_patient_profile_service(),
            registration_service=get_hms_client().registration_service,
            schedule_gateway=schedule_gateway,
        )
    return _patient_sidebar_service
```

在 `patient_agent_backend/app/api/patient.py` 中添加路由：

```python
from app.api.auth import get_patient_profile_service, get_patient_sidebar_service
```

并在 `GET /profile` 之后新增：

```python
@router.get("/sidebar")
async def get_sidebar(session: PatientSession = Depends(require_patient_session)):
    sidebar = await get_patient_sidebar_service().get_sidebar(session.patient_id)
    return sidebar.model_dump()
```

- [ ] **Step 5: 重新运行 API 测试确认通过**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest tests/test_api/test_patient_sidebar_api.py -q
```

Expected: PASS，未登录返回 401，登录后返回聚合结构。

- [ ] **Step 6: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_backend/app/patient_sidebar/schedule_gateway.py \
  patient_agent_backend/app/api/patient.py \
  patient_agent_backend/app/api/auth.py \
  patient_agent_backend/tests/test_api/test_patient_sidebar_api.py && \
git commit -m "feat: add patient sidebar api endpoint"
```

### Task 4: 前端接入真实 sidebar 接口

**Files:**
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx`
- Modify: `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx`
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- Consumes:
  - `patientApi.getSidebar(): Promise<{ data: SidebarResponse }>`
  - `SidebarResponse.profile`
  - `SidebarResponse.recentVisits`
  - `SidebarResponse.schedule`
- Produces:
  - `PatientSidebar` 从接口拉取数据并传入子组件
  - 加载态与错误态 UI

- [ ] **Step 1: 在 API 层新增 sidebar 请求**

在 `patient_agent_frontend/src/api/index.js` 的 `patientApi` 中新增：

```js
  getSidebar() {
    return api.get('/patient/sidebar')
  },
```

- [ ] **Step 2: 改造 `PatientSidebar` 使用接口数据**

将 `patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx` 改为：

```jsx
import { useEffect, useState } from 'react'
import PatientProfileCard from './PatientProfileCard.jsx'
import HospitalScheduleCard from './HospitalScheduleCard.jsx'
import { patientApi } from '../../api/index.js'
import { patientProfile } from '../../mocks/patientProfile.js'
import { scheduleDateLabel, scheduleDepartments } from '../../mocks/scheduleData.js'

const fallbackSidebar = {
  profile: patientProfile,
  recentVisits: patientProfile.recentVisits,
  schedule: {
    dateLabel: scheduleDateLabel,
    departments: scheduleDepartments,
  },
}

export default function PatientSidebar({ user, onSendChat }) {
  const [sidebar, setSidebar] = useState(fallbackSidebar)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)

  useEffect(() => {
    let active = true

    patientApi.getSidebar()
      .then((res) => {
        if (!active) return
        setSidebar(res.data)
        setLoadFailed(false)
      })
      .catch(() => {
        if (!active) return
        setLoadFailed(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  return (
    <aside className="patient-sidebar">
      <PatientProfileCard profile={{ ...sidebar.profile, recentVisits: sidebar.recentVisits }} loading={loading} loadFailed={loadFailed} />
      <HospitalScheduleCard
        user={user}
        onSendChat={onSendChat}
        departments={sidebar.schedule.departments}
        dateLabel={sidebar.schedule.dateLabel}
        loading={loading}
      />
    </aside>
  )
}
```

- [ ] **Step 3: 为卡片增加轻量加载/空态支持**

在 `patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx` 中调整签名：

```jsx
export default function PatientProfileCard({ profile, loading, loadFailed }) {
```

并在 return 里加入状态块：

```jsx
      {loading && <div className="patient-card-hint">正在加载患者信息...</div>}
      {loadFailed && <div className="patient-card-hint">接口加载失败，当前展示本地示例数据</div>}
```

在 `patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx` 中调整签名：

```jsx
export default function HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading }) {
```

并在排班占位前增加：

```jsx
      {loading && <div className="schedule-loading">正在加载医院排班...</div>}
```

- [ ] **Step 4: 补充样式并运行前端构建**

在 `patient_agent_frontend/src/index.css` 中追加：

```css
.patient-card-hint,
.schedule-loading {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #F8FAFC;
  color: #64748B;
  font-size: 12px;
  border: 1px solid #E2E8F0;
}
```

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: `vite build` 成功。

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_frontend/src/api/index.js \
  patient_agent_frontend/src/components/sidebar/PatientSidebar.jsx \
  patient_agent_frontend/src/components/sidebar/PatientProfileCard.jsx \
  patient_agent_frontend/src/components/sidebar/HospitalScheduleCard.jsx \
  patient_agent_frontend/src/index.css && \
git commit -m "feat: load patient sidebar data from backend api"
```

### Task 5: 运行完整验证

**Files:**
- Modify: `patient_agent_backend/app/api/patient.py`
- Modify: `patient_agent_backend/app/patient_sidebar/*.py`
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/components/sidebar/*.jsx`

**Interfaces:**
- Consumes: 已实现的 `GET /api/patient/sidebar`；前端 sidebar 接口接线
- Produces: 可通过测试、可构建、具备真实接口接入能力的右侧栏改造

- [ ] **Step 1: 运行后端 sidebar 相关测试**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && pytest \
  tests/test_patient_sidebar/test_adapters.py \
  tests/test_patient_sidebar/test_service.py \
  tests/test_api/test_patient_sidebar_api.py -q
```

Expected: PASS，所有新测试通过。

- [ ] **Step 2: 运行前端构建**

Run:

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

Expected: PASS，`vite build` 成功。

- [ ] **Step 3: 联调检查**

核对以下行为：

```text
1. 患者登录后访问右侧栏
2. 个人信息显示真实姓名、性别、年龄、脱敏手机号、身份证后四位
3. 近期就诊记录最多显示 3 条，按日期倒序
4. 医院排班按科室显示真实医生与时段
5. 排班为空时右侧栏不白屏
6. 点击“预约挂号”后弹窗仍正常显示
```

- [ ] **Step 4: Commit**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add \
  patient_agent_backend/app/api/patient.py \
  patient_agent_backend/app/api/auth.py \
  patient_agent_backend/app/patient_sidebar \
  patient_agent_backend/app/hms_client/services/registration_service.py \
  patient_agent_frontend/src/api/index.js \
  patient_agent_frontend/src/components/sidebar \
  patient_agent_frontend/src/index.css \
  patient_agent_backend/tests/test_patient_sidebar \
  patient_agent_backend/tests/test_api/test_patient_sidebar_api.py && \
git commit -m "feat: connect patient sidebar to backend data"
```
