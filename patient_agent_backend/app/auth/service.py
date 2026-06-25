import uuid
from datetime import datetime

from app.auth.models import PatientSession


class AuthService:
    def __init__(self, redis_client):
        self._redis = redis_client

    async def create_session(self, phone: str, name: str, patient_id: int) -> PatientSession:
        token = str(uuid.uuid4())
        session = PatientSession(
            token=token,
            patient_id=patient_id,
            phone=phone,
            name=name,
            login_time=datetime.now().isoformat(),
        )
        key = self._get_key(token)
        await self._redis.hset(key, mapping=session.model_dump())
        await self._redis.expire(key, 86400 * 7)
        return session

    async def get_session(self, token: str):
        key = self._get_key(token)
        if hasattr(self._redis, "hgetall"):
            data = await self._redis.hgetall(key)
            if data:
                return PatientSession(
                    token=data["token"],
                    patient_id=int(data["patient_id"]),
                    phone=data["phone"],
                    name=data["name"],
                    login_time=data["login_time"],
                )
        return None

    async def logout(self, token: str) -> None:
        await self._redis.delete(self._get_key(token))

    @staticmethod
    def _get_key(token: str) -> str:
        return f"patient:token:{token}"
