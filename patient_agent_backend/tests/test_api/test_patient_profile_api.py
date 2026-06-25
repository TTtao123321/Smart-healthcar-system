from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import require_patient_session
from app.patient_profile.models import PatientProfile


class FakeSession:
    token = "token-1"
    patient_id = 12
    name = "张三"
    phone = "13800138000"


class FakeProfileService:
    async def get_by_id(self, patient_id: int):
        return PatientProfile(
            id=patient_id,
            uuid="u12",
            name="张三",
            sex="男",
            tel="13800138000",
        )

    async def update_profile(self, patient_id: int, payload):
        return PatientProfile(
            id=patient_id,
            uuid="u12",
            name=payload.name or "张三",
            sex=payload.sex or "男",
            tel="13800138000",
        )


def create_client(monkeypatch):
    from app.api import patient as patient_module
    from app.api.patient import router as patient_router

    monkeypatch.setattr(
        patient_module,
        "get_patient_profile_service",
        lambda: FakeProfileService(),
        raising=False,
    )
    app = FastAPI()
    app.include_router(patient_router)
    app.dependency_overrides[require_patient_session] = lambda: FakeSession()
    return TestClient(app)


def test_get_profile_returns_current_patient_profile(monkeypatch):
    client = create_client(monkeypatch)

    response = client.get("/api/patient/profile", headers={"Authorization": "Bearer token-1"})

    assert response.status_code == 200
    assert response.json()["id"] == 12
    assert response.json()["name"] == "张三"


def test_update_profile_does_not_allow_tel_change(monkeypatch):
    client = create_client(monkeypatch)

    response = client.post(
        "/api/patient/profile",
        headers={"Authorization": "Bearer token-1"},
        json={"name": "李四", "tel": "13900139000"},
    )

    assert response.status_code == 422
