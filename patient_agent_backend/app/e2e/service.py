from copy import deepcopy

from app.e2e.fixtures import BASELINE_HISTORY, BASELINE_SIDEBAR, BASELINE_THREADS


class PatientAgentE2EService:
    def __init__(self, *, phone: str, code: str, patient_id: int, patient_name: str):
        self.phone = phone
        self.code = code
        self.patient_id = patient_id
        self.patient_name = patient_name
        self._scenario = "baseline"
        self._state: dict[str, object] = {}
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
