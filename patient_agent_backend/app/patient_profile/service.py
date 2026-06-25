import uuid
from typing import Optional

from app.patient_profile.models import PatientProfile, PatientProfileUpdate


class PatientProfileService:
    def __init__(self, repository):
        self._repository = repository

    async def get_or_create_by_phone(self, phone: str) -> PatientProfile:
        profile = await self._repository.get_by_phone(phone)
        if profile is not None:
            return profile
        created = PatientProfile(
            id=0,
            uuid=uuid.uuid4().hex,
            name=f"患者{phone[-4:]}",
            tel=phone,
        )
        return await self._repository.create_patient(created)

    async def get_by_id(self, patient_id: int) -> Optional[PatientProfile]:
        return await self._repository.get_by_id(patient_id)

    async def update_profile(self, patient_id: int, payload: PatientProfileUpdate) -> PatientProfile:
        return await self._repository.update_patient_basic_info(patient_id, payload)
