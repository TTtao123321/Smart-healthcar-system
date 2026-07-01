# Patient Results Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add patient-facing medical record and prescription queries, secure them to the logged-in patient, and connect recent-visit sidebar actions to result details.

**Architecture:** Extend HMS with patient-only read endpoints that return masked DTOs rather than backend admin payloads. Update `patient_agent_backend` with new HMS clients, tools, and pre-routing so “我的病历”“我的处方” resolve deterministically, and enhance sidebar recent visits with result availability flags.

**Tech Stack:** Spring Boot, Sa-Token, MyBatis XML mappers, FastAPI, LangGraph tool runtime, Pydantic, pytest

## Global Constraints

- Do not expose existing admin record/prescription payloads directly to patients.
- Every patient-facing query must resolve `patient_id` from session context and re-check ownership at the HMS layer.
- Return masked patient-visible DTOs for diagnosis and medication instructions.
- Reuse the existing sidebar-to-chat interaction pattern; do not add a new patient page.
- High-certainty result intents should be handled in pre-router logic before LLM free-form reasoning.

---

### Task 1: Add HMS Patient-Facing Medical Record and Prescription APIs

**Files:**
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientMedicalRecordsForm.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientMedicalRecordDetailForm.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientPrescriptionsForm.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientPrescriptionDetailForm.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/PatientResultController.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientResultService.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientResultServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/PatientDao.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/PatientResultControllerTest.java`

**Interfaces:**
- Consumes: existing patient ownership data in `patient`, `medical_record`, `prescription`, `prescription_item`, `medical_registration`
- Produces:
  - `POST /patient/medical-records`
  - `POST /patient/medical-records/detail`
  - `POST /patient/prescriptions`
  - `POST /patient/prescriptions/detail`
  - service methods `List<HashMap<String, Object>> selectPatientMedicalRecords(Integer patientId, String startDate, String endDate)` and `HashMap<String, Object> selectPatientPrescriptionDetail(Integer patientId, Integer prescriptionId)`

- [ ] **Step 1: Write the failing test**

```java
@Test
void medicalRecordsEndpointShouldOnlyReturnOwnedRecords() throws Exception {
    when(patientResultService.selectPatientMedicalRecords(7, null, null))
            .thenReturn(List.of(new HashMap<>() {{
                put("medicalRecordId", 101);
                put("visitDate", "2026-07-01");
                put("doctorName", "张医生");
            }}));

    mockMvc.perform(post("/patient/medical-records")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"patientId\":7}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.result[0].medicalRecordId").value(101));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./mvnw -pl hospital_hms_api -Dtest=PatientResultControllerTest test`
Expected: FAIL because `PatientResultController` and the new patient-facing endpoints do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```java
@RestController
@RequestMapping("/patient")
public class PatientResultController {
    @Autowired
    private PatientResultService patientResultService;

    @PostMapping("/medical-records")
    public CommonResult selectMedicalRecords(@RequestBody @Valid SelectPatientMedicalRecordsForm form) {
        return CommonResult.ok().put("result",
                patientResultService.selectPatientMedicalRecords(form.getPatientId(), form.getStartDate(), form.getEndDate()));
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./mvnw -pl hospital_hms_api -Dtest=PatientResultControllerTest,MedicalRecordControllerTest,PrescriptionControllerTest test`
Expected: PASS and the new controller returns patient-scoped payloads.

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientMedicalRecordsForm.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientMedicalRecordDetailForm.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientPrescriptionsForm.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/form/SelectPatientPrescriptionDetailForm.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/PatientResultController.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/PatientResultService.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientResultServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/PatientDao.java \
        hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml \
        hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/PatientResultControllerTest.java
git commit -m "feat(hms): add patient-facing result query endpoints"
```

### Task 2: Add Patient-Visible DTO Mapping and Ownership Checks

**Files:**
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientResultServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/PatientResultServiceImplTest.java`

**Interfaces:**
- Consumes: raw DAO rows for medical records, prescriptions, prescription items
- Produces:
  - list DTO fields `medicalRecordId`, `visitDate`, `department`, `doctorName`, `chiefComplaintSummary`, `status`
  - detail DTO fields `diagnosisSummary`, `instructionSummary`, `items`

- [ ] **Step 1: Write the failing test**

```java
@Test
void prescriptionDetailShouldMaskInternalNotes() {
    when(patientDao.selectPrescriptionDetailByPatientId(7, 88))
            .thenReturn(new HashMap<>() {{
                put("prescriptionId", 88);
                put("usage", "口服，每日三次，医生内部备注：术后随访");
            }});

    HashMap<String, Object> result = service.selectPatientPrescriptionDetail(7, 88);

    assertThat(result.get("usage")).isEqualTo("口服，每日三次");
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./mvnw -pl hospital_hms_api -Dtest=PatientResultServiceImplTest#prescriptionDetailShouldMaskInternalNotes test`
Expected: FAIL because DTO masking logic is not implemented.

- [ ] **Step 3: Write minimal implementation**

```java
private String maskUsage(String usage) {
    if (usage == null) {
        return "";
    }
    return usage.replaceAll("，?医生内部备注[:：].*$", "");
}

private HashMap<String, Object> buildPrescriptionDetail(HashMap<String, Object> row, List<HashMap<String, Object>> items) {
    HashMap<String, Object> result = new HashMap<>();
    result.put("prescriptionId", row.get("prescriptionId"));
    result.put("usage", maskUsage((String) row.get("usage")));
    result.put("items", items);
    return result;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./mvnw -pl hospital_hms_api -Dtest=PatientResultServiceImplTest test`
Expected: PASS for ownership failures and masked patient-visible DTO behavior.

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientResultServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/PatientDao.xml \
        hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/PatientResultServiceImplTest.java
git commit -m "feat(hms): mask patient result payloads"
```

### Task 3: Extend patient_agent HMS Client and Tools

**Files:**
- Create: `patient_agent_backend/app/hms_client/services/medical_record_service.py`
- Create: `patient_agent_backend/app/hms_client/services/prescription_service.py`
- Modify: `patient_agent_backend/app/hms_client/services/__init__.py`
- Modify: `patient_agent_backend/app/hms_client/models.py`
- Modify: `patient_agent_backend/app/hms_client/contract.py`
- Create: `patient_agent_backend/app/tools/result_tools.py`
- Modify: `patient_agent_backend/app/tools/__init__.py`
- Test: `patient_agent_backend/tests/test_hms_client/test_medical_record_service.py`
- Test: `patient_agent_backend/tests/test_hms_client/test_prescription_service.py`
- Test: `patient_agent_backend/tests/test_tools/test_result_tools.py`

**Interfaces:**
- Consumes: new HMS patient-facing endpoints from Task 1
- Produces:
  - client methods `query_my_medical_records()`, `get_medical_record_detail()`, `query_my_prescriptions()`, `get_prescription_detail()`
  - tool names `query_my_medical_records`, `get_medical_record_detail`, `query_my_prescriptions`, `get_prescription_detail`

- [ ] **Step 1: Write the failing test**

```python
async def test_query_my_medical_records_uses_logged_in_patient_context(monkeypatch):
    set_patient_id(7)
    response = await query_my_medical_records.ainvoke({"start_date": "2026-06-01", "end_date": "2026-07-01"})
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["data"][0]["medicalRecordId"] == 101
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_tools/test_result_tools.py -v`
Expected: FAIL because the result services and tools do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
@tool
async def query_my_medical_records(start_date: str | None = None, end_date: str | None = None) -> str:
    patient_id = _require_session_patient_id()
    result = await hms_client.medical_record_service.query_patient_records(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
    )
    return ok(f"共找到 {len(result.items)} 条病历记录", [item.model_dump() for item in result.items])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_hms_client/test_medical_record_service.py tests/test_hms_client/test_prescription_service.py tests/test_tools/test_result_tools.py -v`
Expected: PASS and the new tools only resolve records for the current patient context.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/hms_client/services/medical_record_service.py \
        patient_agent_backend/app/hms_client/services/prescription_service.py \
        patient_agent_backend/app/hms_client/services/__init__.py \
        patient_agent_backend/app/hms_client/models.py \
        patient_agent_backend/app/hms_client/contract.py \
        patient_agent_backend/app/tools/result_tools.py \
        patient_agent_backend/app/tools/__init__.py \
        patient_agent_backend/tests/test_hms_client/test_medical_record_service.py \
        patient_agent_backend/tests/test_hms_client/test_prescription_service.py \
        patient_agent_backend/tests/test_tools/test_result_tools.py
git commit -m "feat(patient-agent): add patient result tools"
```

### Task 4: Add Pre-Router and Sidebar Result Entry Points

**Files:**
- Modify: `patient_agent_backend/app/chat/pre_router.py`
- Modify: `patient_agent_backend/app/patient_sidebar/models.py`
- Modify: `patient_agent_backend/app/patient_sidebar/adapters.py`
- Modify: `patient_agent_backend/app/patient_sidebar/service.py`
- Modify: `patient_agent_backend/app/patient_sidebar/actions.py`
- Modify: `patient_agent_backend/tests/test_api/test_sidebar_action_api.py`
- Modify: `patient_agent_backend/tests/test_patient_sidebar/test_service.py`
- Modify: `patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py`

**Interfaces:**
- Consumes: new result tools from Task 3 and existing sidebar action message flow
- Produces:
  - sidebar fields `hasMedicalRecord: bool`, `hasPrescription: bool`, `latestResultStatus: str`
  - action literals `view_recent_medical_record`, `view_recent_prescription`
  - pre-router intent handlers for “我的病历” and “我的处方”

- [ ] **Step 1: Write the failing test**

```python
async def test_pre_router_handles_my_prescriptions_without_llm(orchestrator):
    result = await orchestrator.handle_chat(
        patient_id=7,
        thread_id="thread-1",
        message="我的处方",
    )

    assert "处方" in result.message
    assert result.metadata["handled_by"] == "pre_router"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_api/test_chat_orchestrator_pre_router.py tests/test_patient_sidebar/test_service.py -k "prescriptions or sidebar" -v`
Expected: FAIL because the pre-router and sidebar actions do not know these intents yet.

- [ ] **Step 3: Write minimal implementation**

```python
class SidebarActionRequest(BaseModel):
    action: Literal["confirm_registration", "view_recent_medical_record", "view_recent_prescription"]
    thread_id: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_api/test_chat_orchestrator_pre_router.py tests/test_api/test_sidebar_action_api.py tests/test_patient_sidebar/test_service.py -v`
Expected: PASS and sidebar clicks enter the same chat thread with result-detail context.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/chat/pre_router.py \
        patient_agent_backend/app/patient_sidebar/models.py \
        patient_agent_backend/app/patient_sidebar/adapters.py \
        patient_agent_backend/app/patient_sidebar/service.py \
        patient_agent_backend/app/patient_sidebar/actions.py \
        patient_agent_backend/tests/test_api/test_sidebar_action_api.py \
        patient_agent_backend/tests/test_patient_sidebar/test_service.py \
        patient_agent_backend/tests/test_api/test_chat_orchestrator_pre_router.py
git commit -m "feat(patient-agent): route patient result intents through sidebar and pre-router"
```
