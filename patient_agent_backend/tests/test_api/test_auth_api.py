from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import auth as auth_module
from app.api.auth import router as auth_router


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.hashes = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)
        self.hashes.pop(key, None)

    async def hset(self, key, mapping):
        self.hashes[key] = dict(mapping)

    async def expire(self, key, ttl):
        return True


class FakeProfile:
    id = 12
    name = "张三"


class FakeProfileService:
    async def get_or_create_by_phone(self, phone: str):
        return FakeProfile()


class FakeAuthService:
    async def create_session(self, phone: str, name: str, patient_id: int):
        return type(
            "Session",
            (),
            {"token": "token-1", "patient_id": patient_id, "name": name, "phone": phone},
        )()

    async def logout(self, token: str):
        return None


def create_client():
    app = FastAPI()
    app.include_router(auth_router)
    auth_module.set_redis(FakeRedis())
    return TestClient(app)


def test_login_returns_real_patient_id(monkeypatch):
    monkeypatch.setattr(
        auth_module,
        "get_patient_profile_service",
        lambda: FakeProfileService(),
        raising=False,
    )
    monkeypatch.setattr(
        auth_module,
        "get_auth_service",
        lambda: FakeAuthService(),
        raising=False,
    )
    client = create_client()
    sms_response = client.post("/api/auth/send-sms", json={"phone": "13800138000"})
    code = sms_response.json()["code_dev"]

    response = client.post("/api/auth/login", json={"phone": "13800138000", "code": code})

    assert response.status_code == 200
    assert response.json()["patient_id"] == 12
    assert response.json()["name"] == "张三"


def test_logout_requires_bearer_token():
    client = create_client()

    response = client.post("/api/auth/logout")

    assert response.status_code == 401
