from copy import deepcopy

from fastapi import HTTPException

from app.auth.models import PatientSession
from app.e2e.fixtures import BASELINE_HISTORY, BASELINE_SIDEBAR, BASELINE_THREADS


class PatientAgentE2EService:
    def __init__(self, *, phone: str, code: str, patient_id: int, patient_name: str):
        self.phone = phone
        self.code = code
        self.patient_id = patient_id
        self.patient_name = patient_name
        self._scenario = "baseline"
        self._login_time = "2026-06-28T00:00:00"
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
            "server_thread_id": "server-thread-9",
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

    async def create_session(self, phone: str, name: str, patient_id: int) -> PatientSession:
        if phone != self.phone or patient_id != self.patient_id:
            raise ValueError("unsupported e2e identity")
        return PatientSession(
            token="e2e-token-1",
            patient_id=self.patient_id,
            phone=self.phone,
            name=self.patient_name,
            login_time=self._login_time,
        )

    async def get_session(self, token: str) -> PatientSession | None:
        if token != "e2e-token-1":
            return None
        return PatientSession(
            token="e2e-token-1",
            patient_id=self.patient_id,
            phone=self.phone,
            name=self.patient_name,
            login_time=self._login_time,
        )

    async def logout(self, token: str) -> None:
        return None

    def list_threads(self, patient_id: int) -> list[dict]:
        self._ensure_patient(patient_id)
        return deepcopy(self._state["threads"])

    def get_history(self, patient_id: int, thread_id: str) -> list[dict]:
        self._ensure_patient(patient_id)
        return deepcopy(self._state["history"].get(thread_id, []))

    def get_sidebar(self, patient_id: int) -> dict:
        self._ensure_patient(patient_id)
        if self._state["sidebar_should_fail"]:
            raise HTTPException(status_code=503, detail="E2E sidebar load failure")
        return deepcopy(self._state["sidebar"])

    def run_sidebar_action(self, *, patient_id: int, action: str, thread_id: str, payload: dict | None) -> dict:
        self._ensure_patient(patient_id)
        if action == "confirm_registration":
            return {
                "message": "已为您确认挂号。",
                "thread_id": self._state["server_thread_id"],
                "needs_handoff": False,
                "reply_type": "assistant",
                "degraded": False,
            }
        return {
            "message": "已收到请求，请稍后查看结果。",
            "thread_id": thread_id,
            "needs_handoff": False,
            "reply_type": "assistant",
            "degraded": False,
        }

    def build_stream_events(self, *, patient_id: int, user_message: str, thread_id: str) -> list[dict]:
        self._ensure_patient(patient_id)
        text = "已收到您的消息。"
        if "继续刚才的话题" in user_message:
            text = "继续为您处理。"
        elif "继续处理刚才那次挂号" in user_message:
            text = "继续处理完成。"
        return [
            {"event": "message", "data": {"content": text, "thread_id": thread_id}},
            {"event": "done", "data": {"thread_id": thread_id}},
        ]

    def delete_thread(self, patient_id: int, thread_id: str) -> None:
        self._ensure_patient(patient_id)
        if self._state["delete_thread_should_fail"]:
            raise HTTPException(status_code=500, detail="删除失败，请稍后重试")
        self._state["threads"] = [item for item in self._state["threads"] if item["thread_id"] != thread_id]
        self._state["history"].pop(thread_id, None)

    def get_profile(self, patient_id: int) -> dict:
        self._ensure_patient(patient_id)
        return deepcopy(self._state["sidebar"]["profile"])

    def _ensure_patient(self, patient_id: int) -> None:
        if patient_id != self.patient_id:
            raise ValueError("unsupported e2e patient")


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
