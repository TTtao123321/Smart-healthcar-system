# Clinician Agent Reuse Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse the existing patient-agent orchestration stack for the hospital-side medical assistant, with clinician-scoped tools for patient record lookup and medical-record draft generation.

**Architecture:** Keep the LangGraph runtime inside `patient_agent_backend`, but introduce a clinician channel with its own prompt, tool whitelist, and RBAC context. Let `hospital_manage_backend` remain the source of authenticated clinician identity and data scope, and have the frontend `medical_assistant.vue` call a real backend flow instead of returning mock text.

**Tech Stack:** FastAPI, LangGraph, Pydantic, Spring Boot RBAC context, Vue 3, Element Plus, pytest

## Global Constraints

- Reuse the existing agent graph and tool runtime; do not fork a separate clinician-specific orchestration engine.
- Clinician requests must carry hospital RBAC context: `userId`, `roleCodes`, `deptScope`, `doctorScope`.
- The first version supports only two clinician capabilities: patient history lookup and draft assistance.
- AI-generated drafts must never be persisted directly to the database; clinicians must review and insert them manually.
- Frontend integration should preserve the current `medical_assistant.vue` layout wherever possible.

---

### Task 1: Introduce Clinician Channel Context and Tool Registry

**Files:**
- Create: `patient_agent_backend/app/clinician/context.py`
- Create: `patient_agent_backend/app/clinician/models.py`
- Create: `patient_agent_backend/app/clinician/tool_registry.py`
- Create: `patient_agent_backend/app/clinician/prompts.py`
- Modify: `patient_agent_backend/app/chat/orchestrator.py`
- Modify: `patient_agent_backend/app/agent/prompts.py`
- Modify: `patient_agent_backend/app/tools/__init__.py`
- Test: `patient_agent_backend/tests/test_api/test_chat_orchestrator.py`
- Test: `patient_agent_backend/tests/test_tools/test_tool_runtime.py`

**Interfaces:**
- Consumes: existing graph compile path and tool runtime from `app/tools/__init__.py`
- Produces:
  - `ClinicianContext(user_id: int, role_codes: list[str], dept_scope: list[int], doctor_scope: list[int])`
  - `get_tools_for_channel(channel: Literal["patient", "clinician"], context: ClinicianContext | None) -> list`
  - clinician prompt template `build_clinician_system_prompt(context: ClinicianContext) -> str`

- [ ] **Step 1: Write the failing test**

```python
def test_clinician_channel_uses_clinician_tool_whitelist():
    context = ClinicianContext(user_id=9, role_codes=["DOCTOR"], dept_scope=[3], doctor_scope=[12])

    tools = get_tools_for_channel("clinician", context)

    assert "query_patient_medical_records" in {tool.name for tool in tools}
    assert "create_registration" not in {tool.name for tool in tools}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_tools/test_tool_runtime.py -k clinician_tool_whitelist -v`
Expected: FAIL because there is no clinician channel context or alternate tool selection path yet.

- [ ] **Step 3: Write minimal implementation**

```python
class ClinicianContext(BaseModel):
    user_id: int
    role_codes: list[str]
    dept_scope: list[int] = Field(default_factory=list)
    doctor_scope: list[int] = Field(default_factory=list)

def get_tools_for_channel(channel: str, context: ClinicianContext | None = None) -> list:
    if channel == "clinician":
        return CLINICIAN_TOOLS
    return PATIENT_TOOLS
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_tools/test_tool_runtime.py tests/test_api/test_chat_orchestrator.py -v`
Expected: PASS and orchestrator can request channel-specific tools without breaking patient flows.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/clinician/context.py \
        patient_agent_backend/app/clinician/models.py \
        patient_agent_backend/app/clinician/tool_registry.py \
        patient_agent_backend/app/clinician/prompts.py \
        patient_agent_backend/app/chat/orchestrator.py \
        patient_agent_backend/app/agent/prompts.py \
        patient_agent_backend/app/tools/__init__.py \
        patient_agent_backend/tests/test_api/test_chat_orchestrator.py \
        patient_agent_backend/tests/test_tools/test_tool_runtime.py
git commit -m "feat(agent-core): add clinician channel context"
```

### Task 2: Add Clinician Patient History and Draft Tools

**Files:**
- Create: `patient_agent_backend/app/tools/clinician_patient_tools.py`
- Create: `patient_agent_backend/app/tools/clinician_record_tools.py`
- Modify: `patient_agent_backend/app/clinician/tool_registry.py`
- Modify: `patient_agent_backend/app/hms_client/models.py`
- Create: `patient_agent_backend/tests/test_tools/test_clinician_patient_tools.py`
- Create: `patient_agent_backend/tests/test_tools/test_clinician_record_tools.py`

**Interfaces:**
- Consumes: clinician context from Task 1 and HMS patient/result endpoints from Phase 2
- Produces:
  - `search_patient_profiles(name: str, phone_suffix: str | None = None) -> str`
  - `query_patient_medical_records(patient_id: int, limit: int = 3) -> str`
  - `get_patient_medical_record_detail(patient_id: int, medical_record_id: int) -> str`
  - `generate_record_draft(chief_complaint: str, patient_summary: str | None = None) -> str`
  - `build_insertable_record_payload(draft_id: str, sections: list[str]) -> str`

- [ ] **Step 1: Write the failing test**

```python
async def test_generate_record_draft_marks_output_as_review_required():
    response = await generate_record_draft.ainvoke({"chief_complaint": "咳嗽3天"})
    payload = json.loads(response)

    assert payload["ok"] is True
    assert payload["data"]["disclaimer"] == "AI 草稿，仅供医生审核"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_tools/test_clinician_record_tools.py -v`
Expected: FAIL because the clinician-only tools do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
@tool
async def generate_record_draft(chief_complaint: str, patient_summary: str | None = None) -> str:
    draft = {
        "chiefComplaint": chief_complaint,
        "presentIllness": f"患者诉{chief_complaint}，症状待医生进一步核实。",
        "physicalExam": "生命体征待完善，建议结合门诊查体结果补充。",
        "disclaimer": "AI 草稿，仅供医生审核",
    }
    return ok("已生成病历草稿", draft)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_tools/test_clinician_patient_tools.py tests/test_tools/test_clinician_record_tools.py -v`
Expected: PASS and clinician tools expose structured history lookup and draft generation.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/tools/clinician_patient_tools.py \
        patient_agent_backend/app/tools/clinician_record_tools.py \
        patient_agent_backend/app/clinician/tool_registry.py \
        patient_agent_backend/app/hms_client/models.py \
        patient_agent_backend/tests/test_tools/test_clinician_patient_tools.py \
        patient_agent_backend/tests/test_tools/test_clinician_record_tools.py
git commit -m "feat(clinician-agent): add record lookup and draft tools"
```

### Task 3: Bridge Hospital RBAC Context into patient_agent_backend

**Files:**
- Create: `patient_agent_backend/app/api/clinician_chat.py`
- Create: `patient_agent_backend/app/auth/clinician_dependencies.py`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/ClinicianAssistantController.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/ClinicianAssistantService.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/ClinicianAssistantServiceImpl.java`
- Test: `patient_agent_backend/tests/test_api/test_clinician_chat_api.py`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/ClinicianAssistantControllerTest.java`

**Interfaces:**
- Consumes: clinician context and clinician tool registry from Tasks 1 and 2
- Produces:
  - `POST /api/clinician/chat`
  - `POST /clinician-assistant/chat`
  - proxy request payload `{message, threadId, userId, roleCodes, deptScope, doctorScope}`

- [ ] **Step 1: Write the failing test**

```java
@Test
void clinicianAssistantControllerShouldProxyCurrentUserContext() throws Exception {
    mockMvc.perform(post("/clinician-assistant/chat")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"message\":\"查一下患者张三的历史病历\"}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.result.channel").value("clinician"));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./mvnw -pl hospital_hms_api -Dtest=ClinicianAssistantControllerTest test && cd patient_agent_backend && pytest tests/test_api/test_clinician_chat_api.py -v`
Expected: FAIL because neither side exposes a clinician-specific chat endpoint yet.

- [ ] **Step 3: Write minimal implementation**

```python
@router.post("/api/clinician/chat")
async def clinician_chat(request: ClinicianChatRequest):
    context = ClinicianContext(
        user_id=request.user_id,
        role_codes=request.role_codes,
        dept_scope=request.dept_scope,
        doctor_scope=request.doctor_scope,
    )
    return await clinician_orchestrator.handle(request.message, request.thread_id, context)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./mvnw -pl hospital_hms_api -Dtest=ClinicianAssistantControllerTest test && cd patient_agent_backend && pytest tests/test_api/test_clinician_chat_api.py tests/test_api/test_chat_orchestrator.py -v`
Expected: PASS and the hospital backend forwards authenticated clinician context to the shared agent runtime.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/api/clinician_chat.py \
        patient_agent_backend/app/auth/clinician_dependencies.py \
        patient_agent_backend/tests/test_api/test_clinician_chat_api.py \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/ClinicianAssistantController.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/ClinicianAssistantService.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/ClinicianAssistantServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/controller/ClinicianAssistantControllerTest.java
git commit -m "feat(clinician-agent): add clinician chat bridge"
```

### Task 4: Replace Frontend Mock Assistant with Real Clinician Chat

**Files:**
- Modify: `hospital_manage_frontend/src/views/medical_assistant.vue`
- Modify: `hospital_manage_frontend/src/router/index.js` if route metadata changes
- Modify: `hospital_manage_frontend/src/views/main.vue` only if assistant menu state or thread persistence hooks are needed
- Test: manual verification checklist in `docs/superpowers/plans/2026-07-01-clinician-agent-reuse-phase3.md`

**Interfaces:**
- Consumes: `/clinician-assistant/chat` backend endpoint from Task 3
- Produces:
  - real thread list state
  - query result cards for patient history
  - draft cards with insert/copy action

- [ ] **Step 1: Write the failing test**

```js
// Manual failure target before implementation:
// 1. Open /medical_assistant
// 2. Enter "查一下患者张三的历史病历"
// 3. Observe that the page still renders the static local fallback copy
// 4. Expected failure: no network request to /clinician-assistant/chat is made
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hospital_manage_frontend && npm run dev`
Expected: The current page still returns the fixed message “正在为您查询相关信息，请稍候……”.

- [ ] **Step 3: Write minimal implementation**

```js
async sendMessage() {
  const text = this.inputText.trim();
  if (!text || this.isTyping) return;
  const conv = this.conversations[this.activeConvIndex];
  conv.messages.push({ role: 'user', content: text });
  this.isTyping = true;
  const { data } = await this.$http.post('/clinician-assistant/chat', {
    message: text,
    threadId: conv.id,
  });
  conv.messages.push({ role: 'assistant', content: data.result.message, payload: data.result.payload || null });
  this.isTyping = false;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hospital_manage_frontend && npm run dev`
Expected:
- Querying a patient history creates a network request to `/clinician-assistant/chat`
- The assistant shows structured results instead of the static placeholder
- Draft responses render “AI 草稿，仅供医生审核”

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_frontend/src/views/medical_assistant.vue \
        hospital_manage_frontend/src/router/index.js \
        hospital_manage_frontend/src/views/main.vue
git commit -m "feat(hospital-frontend): connect medical assistant to clinician agent"
```
