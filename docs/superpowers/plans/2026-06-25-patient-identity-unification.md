# Patient Identity Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `patient_card_id` from the registration flow and unify all patient identity handling on `patient_user_info.id` exposed everywhere as `patient_id`.

**Architecture:** The migration is a direct cutover. The SQL schema, HMS Java backend, Python Agent backend, and nearby tests all rename registration ownership from `patient_card_id` to `patient_id`, while the patient-side session remains the only trusted source of patient identity. Ownership validation for query and cancel flows is enforced in the Agent layer before mutation.

**Tech Stack:** MySQL schema SQL, Spring Boot + MyBatis + JUnit 5, FastAPI + Pydantic + pytest, React + fetch/axios.

## Global Constraints

- 唯一合法患者身份统一为 `patient_user_info.id`
- 删除挂号链路中的 `patient_card_id` 字段和相关业务命名
- 将 `medical_registration` 及其所有上下游依赖统一改为 `patient_id`
- 保证前端、请求体、LLM 工具均不能自由传入患者身份
- 保证聊天、聊天历史、挂号查询、挂号创建、挂号取消均按当前登录患者隔离
- 不引入“常用就诊人”或“代家属挂号”能力
- 不保留 `patient_card_id` 兼容层

---

### Task 1: Rename Registration Ownership In SQL And HMS Create Path

**Files:**
- Modify: `hospital_manage_backend/init-sql/01-init.sql`
- Modify: `hospital_manage_backend/init-sql/04-init-patient-data.sql`
- Modify: `hospital_manage_backend/init-sql/05-init-schedule-test-data.sql`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/schema.sql`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/pojo/MedicalRegistration.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertMedicalRegistrationForm.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/MedicalRegistrationControllerTest.java`

**Interfaces:**
- Consumes: `MedicalRegistrationService.save(MedicalRegistration entity) -> int`
- Produces: `InsertMedicalRegistrationForm.patientId: Integer`, `MedicalRegistration.patientId: Integer`, SQL column `medical_registration.patient_id`

- [ ] **Step 1: Write the failing Java tests for the renamed field**

```java
@Test
@DisplayName("save_正常创建挂号并返回主键")
void save_正常创建挂号并返回主键() {
    MedicalRegistration entity = new MedicalRegistration();
    entity.setPatientId(1);
    entity.setWorkPlanId(10);
    entity.setDoctorScheduleId(100);
    entity.setDoctorId(8);
    entity.setDeptSubId(3);
    entity.setDate("2026-06-25");
    entity.setSlot(1);

    HashMap<String, Object> patient = new HashMap<>();
    patient.put("id", 1);
    when(patientDao.selectPatientInfoById(1)).thenReturn(patient);

    HashMap<String, Object> schedule = new HashMap<>();
    schedule.put("maximum", 10);
    schedule.put("num", 3);
    when(medicalRegistrationDao.selectScheduleById(100)).thenReturn(schedule);

    int id = medicalRegistrationService.save(entity);

    assertEquals(66, id);
}
```

```java
@Test
@DisplayName("save_正常返回成功")
void save_正常返回成功() {
    InsertMedicalRegistrationForm form = new InsertMedicalRegistrationForm();
    form.setPatientId(1);
    form.setWorkPlanId(10);
    form.setDoctorScheduleId(100);
    form.setDoctorId(8);
    form.setDeptSubId(3);
    form.setDate("2026-06-25");
    form.setSlot(1);

    when(medicalRegistrationService.save(any())).thenReturn(66);

    CommonResult result = medicalRegistrationController.save(form);

    assertEquals(200, result.get("code"));
}
```

- [ ] **Step 2: Run the targeted Java tests and confirm compile/test failures mention `setPatientId` or `patientId`**

Run:

```bash
./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest,MedicalRegistrationControllerTest test
```

Expected: FAIL because `MedicalRegistration` and `InsertMedicalRegistrationForm` still expose `patientCardId`.

- [ ] **Step 3: Implement the SQL and Java rename**

```sql
CREATE TABLE `medical_registration`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `patient_id` int(11) NULL DEFAULT NULL COMMENT '患者ID',
  `work_plan_id` int(11) NULL DEFAULT NULL COMMENT '医生出诊计划ID',
  `doctor_schedule_id` int(11) NULL DEFAULT NULL COMMENT '医生排班时段ID',
  `doctor_id` int(11) NULL DEFAULT NULL COMMENT '医生ID',
  `dept_sub_id` int(11) NULL DEFAULT NULL COMMENT '诊室ID',
  `date` date NULL DEFAULT NULL COMMENT '就诊日期',
  `slot` tinyint(4) NULL DEFAULT NULL COMMENT '时间段',
  `status` tinyint(4) NULL DEFAULT 0 COMMENT '就诊状态: 0=待就诊, 1=就诊中, 2=已就诊, 3=复诊中',
  `payment_status` tinyint(4) NULL DEFAULT NULL COMMENT '支付状态',
  `create_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
);
```

```java
@Data
@Schema(description = "创建挂号表单")
public class InsertMedicalRegistrationForm {

    @NotNull(message = "patientId不能为空")
    @Min(value = 1, message = "patientId不能小于1")
    private Integer patientId;

    @NotNull(message = "workPlanId不能为空")
    @Min(value = 1, message = "workPlanId不能小于1")
    private Integer workPlanId;
    // ...keep the remaining fields unchanged
}
```

```java
public int save(MedicalRegistration entity) {
    HashMap<String, Object> patient = patientDao.selectPatientInfoById(entity.getPatientId());
    if (patient == null) {
        throw new GlobalException("患者不存在");
    }
    // existing schedule validation stays unchanged
}
```

```xml
<insert id="insert" parameterType="com.hospital.hms.pojo.MedicalRegistration" useGeneratedKeys="true" keyProperty="id">
    INSERT INTO medical_registration
    (patient_id, work_plan_id, doctor_schedule_id, doctor_id, dept_sub_id, date, slot, status, payment_status)
    VALUES
    (#{patientId}, #{workPlanId}, #{doctorScheduleId}, #{doctorId}, #{deptSubId},
     STR_TO_DATE(#{date}, '%Y-%m-%d'), #{slot}, #{status}, #{paymentStatus})
</insert>
```

- [ ] **Step 4: Run the targeted Java tests and confirm they pass**

Run:

```bash
./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest,MedicalRegistrationControllerTest test
```

Expected: PASS with both tests green.

- [ ] **Step 5: Commit the SQL + HMS create-path rename**

```bash
git add \
  hospital_manage_backend/init-sql/01-init.sql \
  hospital_manage_backend/init-sql/04-init-patient-data.sql \
  hospital_manage_backend/init-sql/05-init-schedule-test-data.sql \
  hospital_manage_backend/hospital_hms_api/src/main/resources/schema.sql \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/pojo/MedicalRegistration.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/InsertMedicalRegistrationForm.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java \
  hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/MedicalRegistrationControllerTest.java
git commit -m "refactor(hms): rename registration patient ownership to patient id"
```

### Task 2: Rename Patient Query Surfaces From patientCardId To patientId

**Files:**
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/PatientDao.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientService.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientRegistrationsForm.java`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/PatientServiceImplTest.java`

**Interfaces:**
- Consumes: `PatientDao.selectPatientInfoById(Integer patientId) -> HashMap<String, Object>`
- Produces: query payloads and result aliases using `patientId`, with SQL joins on `mr.patient_id = pi.id`

- [ ] **Step 1: Write the failing patient query test for the new field name**

```java
@Test
@DisplayName("selectPatientDetail_使用patientId查询患者详情")
void selectPatientDetail_使用patientId查询患者详情() {
    Integer patientId = 1;
    HashMap<String, Object> patientInfo = new HashMap<>();
    patientInfo.put("patientId", 1);
    when(patientDao.selectPatientInfoById(patientId)).thenReturn(patientInfo);

    HashMap<String, Object> result = patientService.selectPatientDetail(patientId, null, null);

    assertEquals(1, result.get("patientId"));
    verify(patientDao).selectPatientInfoById(patientId);
}
```

- [ ] **Step 2: Run the targeted patient service test and confirm failure on old aliases or method names**

Run:

```bash
./mvnw -pl hospital_hms_api -Dtest=PatientServiceImplTest test
```

Expected: FAIL because XML aliases and form fields still use `patientCardId`.

- [ ] **Step 3: Rename query aliases, parameters, and joins**

```xml
SELECT
    mr.patient_id AS patientId,
    mr.dept_sub_id AS deptSubId,
    mr.doctor_id AS doctorId,
    MAX(pi.name) AS name
FROM medical_registration mr
LEFT JOIN patient_user_info pi ON mr.patient_id = pi.id
```

```xml
<select id="selectPatientInfoById" parameterType="int" resultType="java.util.HashMap">
    SELECT
        id AS patientId,
        name, sex, pid, tel, birthday,
        medical_history AS medicalHistory,
        allergy_history AS allergyHistory,
        family_history AS familyHistory,
        insurance_type AS insuranceType
    FROM patient_user_info
    WHERE id = #{patientId}
</select>
```

```java
public HashMap<String, Object> selectPatientDetail(Integer patientId, Integer deptSubId, Integer doctorId) {
    HashMap<String, Object> patientInfo = patientDao.selectPatientInfoById(patientId);
    HashMap<String, Object> param = new HashMap<>();
    param.put("patientId", patientId);
    param.put("deptSubId", deptSubId);
    param.put("doctorId", doctorId);
    // keep existing aggregation behavior
}
```

- [ ] **Step 4: Run the targeted patient service test and confirm it passes**

Run:

```bash
./mvnw -pl hospital_hms_api -Dtest=PatientServiceImplTest test
```

Expected: PASS with the renamed query path and aliases.

- [ ] **Step 5: Commit the patient query rename**

```bash
git add \
  hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/PatientDao.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientService.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientServiceImpl.java \
  hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientRegistrationsForm.java \
  hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/PatientServiceImplTest.java
git commit -m "refactor(hms): rename patient registration query fields"
```

### Task 3: Enforce patient_id Ownership In Agent Registration Flows

**Files:**
- Modify: `patient_agent_backend/app/hms_client/models.py`
- Modify: `patient_agent_backend/app/hms_client/services/registration_service.py`
- Modify: `patient_agent_backend/app/tools/registration_tools.py`
- Modify: `patient_agent_backend/app/patient_sidebar/service.py`
- Test: `patient_agent_backend/tests/test_tools/test_registration_tools_auth.py`
- Test: `patient_agent_backend/tests/test_patient_sidebar/test_service.py`
- Create: `patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py`

**Interfaces:**
- Consumes: `get_patient_id() -> int | None`, `RegistrationService.query(request: RegistrationQueryRequest) -> RegistrationQueryResponse`
- Produces: `RegistrationCreateRequest.patient_id: int`, `RegistrationQueryRequest.patient_id: Optional[int]`, `ensure_owned_registration(registration_id: int, patient_id: int) -> RegistrationItem | None`

- [ ] **Step 1: Write the failing pytest coverage for ownership and renamed fields**

```python
@pytest.mark.asyncio
async def test_query_registration_uses_session_patient_id():
    set_patient_session(type("Session", (), {"patient_id": 88})())
    service = FakeRegistrationService(items=[type("Item", (), {"id": 9, "patient_id": 88, "model_dump": lambda self: {"id": 9, "patient_id": 88}})()])
    tools = create_registration_tools(type("Client", (), {"registration_service": service})())
    query_registration = next(tool for tool in tools if tool.name == "query_registration")

    result = await query_registration.ainvoke({"registration_id": 9})

    assert service.query_requests[0].patient_id == 88
```

```python
@pytest.mark.asyncio
async def test_cancel_registration_rejects_unowned_record():
    set_patient_session(type("Session", (), {"patient_id": 88})())
    service = FakeRegistrationService(items=[])
    tools = create_registration_tools(type("Client", (), {"registration_service": service})())
    cancel_registration = next(tool for tool in tools if tool.name == "cancel_registration")

    payload = json.loads(await cancel_registration.ainvoke({"registration_id": 9}))

    assert payload["ok"] is False
    assert "无权限" in payload["error"]
```

- [ ] **Step 2: Run the targeted pytest files and confirm failures on `patient_card_id`**

Run:

```bash
pytest \
  patient_agent_backend/tests/test_tools/test_registration_tools_auth.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py \
  patient_agent_backend/tests/test_patient_sidebar/test_service.py -q
```

Expected: FAIL because models and tools still use `patient_card_id` and `cancel_registration` does not verify ownership.

- [ ] **Step 3: Rename models and implement ownership checks**

```python
class RegistrationCreateRequest(BaseModel):
    patient_id: int
    work_plan_id: int
    doctor_schedule_id: int
    doctor_id: int
    dept_sub_id: int
    appointment_date: date_type
    slot: int


class RegistrationQueryRequest(BaseModel):
    patient_id: Optional[int] = None
    registration_id: Optional[int] = None
```

```python
async def query(self, request: RegistrationQueryRequest) -> RegistrationQueryResponse:
    payload = {"page": 1, "length": 20}
    if request.patient_id:
        payload["patientId"] = request.patient_id
    if request.registration_id:
        payload["id"] = request.registration_id
```

```python
def _require_session_patient_id() -> int:
    patient_id = get_patient_id()
    if patient_id is None:
        raise ValueError("请先登录后再挂号")
    return int(patient_id)


async def _load_owned_registration(registration_id: int, patient_id: int):
    result = await hms_client.registration_service.query(
        RegistrationQueryRequest(patient_id=patient_id, registration_id=registration_id)
    )
    items = getattr(result, "items", [])
    return items[0] if items else None
```

```python
@tool
async def cancel_registration(registration_id: int) -> str:
    try:
        patient_id = _require_session_patient_id()
    except ValueError as e:
        return err(str(e), "请先引导用户完成登录。")

    item = await _load_owned_registration(registration_id, patient_id)
    if item is None:
        return err("记录不存在或无权限", "请告知用户只能取消本人挂号记录。")

    result = await hms_client.registration_service.cancel(
        RegistrationCancelRequest(registration_id=registration_id)
    )
    return ok("挂号已取消", result.model_dump())
```

- [ ] **Step 4: Run the targeted pytest files and confirm they pass**

Run:

```bash
pytest \
  patient_agent_backend/tests/test_tools/test_registration_tools_auth.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py \
  patient_agent_backend/tests/test_patient_sidebar/test_service.py -q
```

Expected: PASS with the renamed request fields and ownership validation.

- [ ] **Step 5: Commit the Agent registration hardening**

```bash
git add \
  patient_agent_backend/app/hms_client/models.py \
  patient_agent_backend/app/hms_client/services/registration_service.py \
  patient_agent_backend/app/tools/registration_tools.py \
  patient_agent_backend/app/patient_sidebar/service.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_auth.py \
  patient_agent_backend/tests/test_tools/test_registration_tools_ownership.py \
  patient_agent_backend/tests/test_patient_sidebar/test_service.py
git commit -m "feat(agent): enforce patient ownership in registration flows"
```

### Task 4: Verify Chat Isolation And Remove Stray Frontend Identity Inputs

**Files:**
- Modify: `patient_agent_frontend/src/api/index.js`
- Modify: `patient_agent_frontend/src/App.jsx`
- Test: `patient_agent_backend/tests/test_api/test_chat_auth.py`
- Optional Test: `patient_agent_frontend/src/components/sidebar/sidebar-workbench.test.jsx`

**Interfaces:**
- Consumes: `chatApi.send(message: string, threadId?: string)`, `chatApi.sendStream(message: string, threadId?: string)`
- Produces: requests that never include `patient_id` or `patient_card_id` in the body; chat backend tests proving forwarded identity is ignored

- [ ] **Step 1: Extend the existing chat auth test to keep guarding against forged identity**

```python
def test_chat_ignores_forwarded_patient_id():
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer token-1"},
        json={"message": "你好", "patient_id": 999, "thread_id": "t-1"},
    )

    assert response.status_code == 200
    assert graph.state["patient_id"] == 88
    assert memory.loaded[0][0] == 88
```

```python
def test_chat_history_uses_authenticated_patient_id():
    response = client.get(
        "/api/chat/history",
        headers={"Authorization": "Bearer token-1"},
        params={"patient_id": 999, "thread_id": "t-2"},
    )

    assert response.status_code == 200
    assert memory.loaded[0][0] == 88
```

- [ ] **Step 2: Run backend auth tests and a frontend grep check**

Run:

```bash
pytest patient_agent_backend/tests/test_api/test_chat_auth.py -q
grep -R "patient_card_id\\|patientCardId" patient_agent_frontend/src patient_agent_backend/app || true
```

Expected: pytest PASS or stays green; grep still reports old backend references before cleanup is complete.

- [ ] **Step 3: Remove any remaining frontend identity submission and keep only token-based auth**

```javascript
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
const { token, patient_id, name } = res.data
const userInfo = { name, token, patient_id, phone }
localStorage.setItem(STORAGE_KEYS.TOKEN, token)
saveToStorage(STORAGE_KEYS.USER, userInfo)
```

- [ ] **Step 4: Run final focused verification for chat isolation and search for removed names**

Run:

```bash
pytest patient_agent_backend/tests/test_api/test_chat_auth.py -q
grep -R "patient_card_id\\|patientCardId" \
  hospital_manage_backend/hospital_hms_api/src \
  hospital_manage_backend/init-sql \
  patient_agent_backend/app \
  patient_agent_backend/tests \
  patient_agent_frontend/src || true
```

Expected: pytest PASS; grep returns no business-effective code references, or only spec/history files outside the implementation target.

- [ ] **Step 5: Commit the final cleanup and verification**

```bash
git add \
  patient_agent_frontend/src/api/index.js \
  patient_agent_frontend/src/App.jsx \
  patient_agent_backend/tests/test_api/test_chat_auth.py
git commit -m "test(auth): keep patient identity isolated by session"
```

## Self-Review

- **Spec coverage:** Task 1 covers SQL schema plus HMS create-path rename. Task 2 covers HMS patient query surfaces and result aliases. Task 3 covers Python HMS client, tools, sidebar naming, and ownership enforcement. Task 4 covers chat isolation guardrails plus final cross-repo cleanup verification.
- **Placeholder scan:** No `TODO`, `TBD`, “implement later”, or “write tests” placeholders remain. Every task includes concrete files, snippets, commands, and expected outcomes.
- **Type consistency:** The plan consistently uses `patient_id` in SQL, Java fields, JSON payloads, Pydantic models, and tool/session ownership checks.
