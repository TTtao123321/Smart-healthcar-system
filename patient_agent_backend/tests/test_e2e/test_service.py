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
