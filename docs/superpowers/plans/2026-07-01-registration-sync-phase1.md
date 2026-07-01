# Registration Sync Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build transactional schedule inventory updates, RabbitMQ event broadcasting, and patient-side notification/remaining-slot sync for registration lifecycle changes.

**Architecture:** Keep `hospital_hms_api` as the only source of truth for schedules and registrations. Execute inventory changes inside HMS database transactions, publish domain events after commit, and let `patient_agent_backend` consume events to refresh sidebar notifications while schedule queries still read HMS in real time.

**Tech Stack:** Spring Boot, MyBatis XML mappers, MySQL, RabbitMQ, Redis, FastAPI, Pydantic, pytest

## Global Constraints

- Do not create a duplicate inventory table; reuse `doctor_work_plan_schedule.maximum` and `doctor_work_plan_schedule.num`.
- All registration create/cancel logic must be committed in HMS before publishing RabbitMQ events.
- Patient-visible schedule availability must come from real-time HMS query results, not from a local cache in `patient_agent_backend`.
- First release only supports in-app notification and sidebar updates; no SMS gateway integration.
- Event consumers must be idempotent using `eventId`.

---

### Task 1: Harden HMS Registration Transaction

**Files:**
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/MedicalRegistrationService.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/MedicalRegistrationDao.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/schema.sql`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java`

**Interfaces:**
- Consumes: existing `int save(MedicalRegistration entity)` entrypoint and `int updateRegistrationStatus(Integer id, Integer status)` patient update flow
- Produces:
  - `int save(MedicalRegistration entity)` with row-locking and bounded inventory update
  - `int cancelRegistration(Integer registrationId)` in `MedicalRegistrationService`
  - mapper methods `HashMap<String, Object> selectScheduleForUpdate(Integer scheduleId)`, `int decreaseScheduleNum(Integer scheduleId)`, `HashMap<String, Object> selectRegistrationById(Integer registrationId)`

- [ ] **Step 1: Write the failing test**

```java
@Test
void saveShouldRejectWhenLockedScheduleIsFull() {
    MedicalRegistration entity = buildRegistration(1001, 2001, 3001, 4001);

    when(patientDao.selectPatientInfoById(1001)).thenReturn(new HashMap<>());
    when(medicalRegistrationDao.selectScheduleForUpdate(2001))
            .thenReturn(new HashMap<>() {{
                put("maximum", 1);
                put("num", 1);
                put("workPlanStatus", "ACTIVE");
            }});

    assertThatThrownBy(() -> service.save(entity))
            .isInstanceOf(GlobalException.class)
            .hasMessageContaining("当前号源已满");
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest#saveShouldRejectWhenLockedScheduleIsFull test`
Expected: FAIL because `selectScheduleForUpdate()` and the stricter validation do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```java
public interface MedicalRegistrationService {
    int save(MedicalRegistration entity);
    int cancelRegistration(Integer registrationId);
}

@Transactional
public int save(MedicalRegistration entity) {
    HashMap<String, Object> schedule = medicalRegistrationDao.selectScheduleForUpdate(entity.getDoctorScheduleId());
    int maximum = MapUtil.getInt(schedule, "maximum", 0);
    int num = MapUtil.getInt(schedule, "num", 0);
    String workPlanStatus = MapUtil.getStr(schedule, "workPlanStatus", "ACTIVE");
    if (!"ACTIVE".equals(workPlanStatus)) {
        throw new GlobalException("当前排班已停诊");
    }
    if (num >= maximum) {
        throw new GlobalException("当前号源已满");
    }
    entity.setStatus(0);
    entity.setPaymentStatus(0);
    medicalRegistrationDao.insert(entity);
    medicalRegistrationDao.increaseScheduleNum(entity.getDoctorScheduleId());
    return entity.getId();
}

@Transactional
public int cancelRegistration(Integer registrationId) {
    HashMap<String, Object> registration = medicalRegistrationDao.selectRegistrationById(registrationId);
    if (registration == null) {
        throw new GlobalException("挂号记录不存在");
    }
    medicalRegistrationDao.updateRegistrationStatus(registrationId, -1);
    medicalRegistrationDao.decreaseScheduleNum((Integer) registration.get("doctorScheduleId"));
    return 1;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest test`
Expected: PASS for the new failure case and existing save behavior.

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/MedicalRegistrationService.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/PatientServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/dao/MedicalRegistrationDao.java \
        hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/MedicalRegistrationDao.xml \
        hospital_manage_backend/hospital_hms_api/src/main/resources/schema.sql \
        hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java
git commit -m "feat(hms): harden registration inventory transaction"
```

### Task 2: Publish HMS Domain Events

**Files:**
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/config/RabbitMqConfig.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/HmsDomainEvent.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/HmsDomainEventPublisher.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/RegistrationEventPayload.java`
- Create: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/ScheduleEventPayload.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/DoctorWorkPlanScheduleServiceImpl.java`
- Test: `hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java`

**Interfaces:**
- Consumes: transactional save/cancel logic from Task 1
- Produces:
  - `void publishAfterCommit(HmsDomainEvent<?> event)`
  - route keys `registration.created`, `registration.cancelled`, `schedule.updated`, `schedule.suspended`

- [ ] **Step 1: Write the failing test**

```java
@Test
void saveShouldPublishRegistrationCreatedEventAfterInsert() {
    MedicalRegistration entity = buildRegistration(1001, 2001, 3001, 4001);
    when(patientDao.selectPatientInfoById(1001)).thenReturn(new HashMap<>());
    when(medicalRegistrationDao.selectScheduleForUpdate(2001)).thenReturn(activeSchedule(3, 1));

    service.save(entity);

    verify(eventPublisher).publishAfterCommit(argThat(event ->
            "registration.created".equals(event.getEventType())
                    && ((RegistrationEventPayload) event.getPayload()).getPatientId().equals(1001)
    ));
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest#saveShouldPublishRegistrationCreatedEventAfterInsert test`
Expected: FAIL because the publisher and event classes do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```java
public record HmsDomainEvent<T>(
        String eventId,
        String eventType,
        Instant occurredAt,
        String traceId,
        String operatorType,
        Integer operatorId,
        T payload
) {}

@Component
public class HmsDomainEventPublisher {
    private final RabbitTemplate rabbitTemplate;

    public void publishAfterCommit(HmsDomainEvent<?> event) {
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                rabbitTemplate.convertAndSend("hms.domain.events", event.eventType(), event);
            }
        });
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./mvnw -pl hospital_hms_api -Dtest=MedicalRegistrationServiceImplTest test`
Expected: PASS with event publish assertions for create/cancel and schedule update entrypoints.

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/config/RabbitMqConfig.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/HmsDomainEvent.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/HmsDomainEventPublisher.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/RegistrationEventPayload.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/event/ScheduleEventPayload.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/MedicalRegistrationServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/DoctorWorkPlanScheduleServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/test/java/com/hospital/hms/service/MedicalRegistrationServiceImplTest.java
git commit -m "feat(hms): publish registration and schedule domain events"
```

### Task 3: Add Remaining Slots and Status to Query Surfaces

**Files:**
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/DoctorWorkPlanScheduleController.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/DoctorWorkPlanScheduleServiceImpl.java`
- Modify: `hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/DoctorWorkPlanScheduleDao.xml`
- Modify: `patient_agent_backend/app/hms_client/models.py`
- Modify: `patient_agent_backend/app/hms_client/services/doctor_service.py`
- Modify: `patient_agent_backend/app/tools/doctor_tools.py`
- Test: `patient_agent_backend/tests/test_hms_client/test_doctor_service.py`

**Interfaces:**
- Consumes: HMS schedule query endpoints
- Produces:
  - HMS response fields `remaining` and `scheduleStatus`
  - patient-side normalized model fields `remaining: int` and `schedule_status: str`

- [ ] **Step 1: Write the failing test**

```python
def test_query_schedule_detail_maps_remaining_and_status(httpx_mock):
    httpx_mock.add_response(
        json={"result": {"doctorId": 7, "maximum": 3, "scheduleStatus": "ACTIVE",
                         "slots": [{"scheduleId": 11, "slot": 2, "num": 1, "remaining": 2}]}}
    )

    result = asyncio.run(service.query_schedule_detail(123))

    assert result.schedule_status == "ACTIVE"
    assert result.slots[0].remaining == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_hms_client/test_doctor_service.py -k remaining_and_status -v`
Expected: FAIL because the HMS client models do not expose `remaining` or `schedule_status`.

- [ ] **Step 3: Write minimal implementation**

```python
class ScheduleSlot(BaseModel):
    schedule_id: int
    slot: int
    num: int
    remaining: int = 0

class ScheduleDetail(BaseModel):
    doctor_id: int
    maximum: int
    schedule_status: str = "ACTIVE"
    slots: list[ScheduleSlot]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_hms_client/test_doctor_service.py tests/test_tools/test_registration_flow_tools.py -v`
Expected: PASS and agent responses now include remaining slot counts.

- [ ] **Step 5: Commit**

```bash
git add hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/controller/DoctorWorkPlanScheduleController.java \
        hospital_manage_backend/hospital_hms_api/src/main/java/com/hospital/hms/service/impl/DoctorWorkPlanScheduleServiceImpl.java \
        hospital_manage_backend/hospital_hms_api/src/main/resources/mapper/DoctorWorkPlanScheduleDao.xml \
        patient_agent_backend/app/hms_client/models.py \
        patient_agent_backend/app/hms_client/services/doctor_service.py \
        patient_agent_backend/app/tools/doctor_tools.py \
        patient_agent_backend/tests/test_hms_client/test_doctor_service.py
git commit -m "feat(schedule): expose remaining slots and schedule status"
```

### Task 4: Consume Events for Sidebar Notifications and HMS Patient Status View

**Files:**
- Create: `patient_agent_backend/app/notifications/__init__.py`
- Create: `patient_agent_backend/app/notifications/models.py`
- Create: `patient_agent_backend/app/notifications/repository.py`
- Create: `patient_agent_backend/app/notifications/consumer.py`
- Modify: `patient_agent_backend/app/main.py`
- Modify: `patient_agent_backend/app/patient_sidebar/models.py`
- Modify: `patient_agent_backend/app/patient_sidebar/service.py`
- Modify: `patient_agent_backend/app/patient_sidebar/actions.py`
- Modify: `patient_agent_backend/app/api/patient.py`
- Test: `patient_agent_backend/tests/test_patient_sidebar/test_service.py`
- Test: `patient_agent_backend/tests/test_api/test_sidebar_action_api.py`

**Interfaces:**
- Consumes: `HmsDomainEvent` messages from `hms.domain.events`
- Produces:
  - `NotificationItem` with `event_id: str`, `kind: str`, `title: str`, `body: str`
  - `SidebarResponse.notifications: list[NotificationItem]`
  - sidebar actions `view_schedule_change` and `view_registration_result`

- [ ] **Step 1: Write the failing test**

```python
async def test_sidebar_includes_recent_notifications():
    service = PatientSidebarService(profile_service, registration_service, schedule_gateway, notification_repository)
    await notification_repository.save(7, NotificationItem(
        event_id="evt-1",
        kind="schedule_suspended",
        title="停诊提醒",
        body="您已挂号的排班已停诊",
    ))

    sidebar = await service.get_sidebar(7)

    assert sidebar.notifications[0].title == "停诊提醒"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd patient_agent_backend && pytest tests/test_patient_sidebar/test_service.py -k notifications -v`
Expected: FAIL because the sidebar model has no notifications field and the consumer does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
class NotificationItem(BaseModel):
    eventId: str
    kind: str
    title: str
    body: str

class SidebarResponse(BaseModel):
    profile: SidebarProfile
    recentVisits: list[SidebarRecentVisit] = Field(default_factory=list)
    schedule: SidebarSchedule
    notifications: list[NotificationItem] = Field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd patient_agent_backend && pytest tests/test_patient_sidebar/test_service.py tests/test_api/test_sidebar_action_api.py -v`
Expected: PASS and sidebar API returns notifications plus the existing data.

- [ ] **Step 5: Commit**

```bash
git add patient_agent_backend/app/notifications \
        patient_agent_backend/app/main.py \
        patient_agent_backend/app/patient_sidebar/models.py \
        patient_agent_backend/app/patient_sidebar/service.py \
        patient_agent_backend/app/patient_sidebar/actions.py \
        patient_agent_backend/app/api/patient.py \
        patient_agent_backend/tests/test_patient_sidebar/test_service.py \
        patient_agent_backend/tests/test_api/test_sidebar_action_api.py
git commit -m "feat(patient-agent): consume hms events for sidebar notifications"
```
