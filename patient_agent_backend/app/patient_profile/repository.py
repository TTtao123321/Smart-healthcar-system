from typing import Optional

import aiomysql

from app.patient_profile.models import PatientProfile, PatientProfileUpdate


class PatientProfileRepository:
    def __init__(self, pool):
        self._pool = pool

    async def get_by_phone(self, phone: str) -> Optional[PatientProfile]:
        sql = """
        SELECT id, uuid, name, sex, pid, tel, birthday,
               insurance_type, medical_history, allergy_history, family_history
        FROM patient_user_info
        WHERE tel=%s
        LIMIT 1
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (phone,))
                row = await cursor.fetchone()
        return self._to_profile(row)

    async def get_by_id(self, patient_id: int) -> Optional[PatientProfile]:
        sql = """
        SELECT id, uuid, name, sex, pid, tel, birthday,
               insurance_type, medical_history, allergy_history, family_history
        FROM patient_user_info
        WHERE id=%s
        LIMIT 1
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (patient_id,))
                row = await cursor.fetchone()
        return self._to_profile(row)

    async def create_patient(self, profile: PatientProfile) -> PatientProfile:
        sql = """
        INSERT INTO patient_user_info(
            uuid, name, sex, pid, tel, birthday, password,
            medical_history, allergy_history, family_history, insurance_type
        )
        VALUES(%s, %s, %s, %s, %s, %s, '', %s, %s, %s, %s)
        """
        params = (
            profile.uuid,
            profile.name,
            profile.sex,
            profile.pid,
            profile.tel,
            profile.birthday,
            profile.medical_history,
            profile.allergy_history,
            profile.family_history,
            profile.insurance_type,
        )
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params)
                patient_id = cursor.lastrowid
        return profile.model_copy(update={"id": patient_id})

    async def update_patient_basic_info(
        self, patient_id: int, payload: PatientProfileUpdate
    ) -> PatientProfile:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            current = await self.get_by_id(patient_id)
            if current is None:
                raise ValueError("患者档案不存在")
            return current

        columns = ", ".join(f"{field}=%s" for field in updates.keys())
        sql = f"UPDATE patient_user_info SET {columns} WHERE id=%s"
        params = tuple(updates.values()) + (patient_id,)
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params)
        updated = await self.get_by_id(patient_id)
        if updated is None:
            raise ValueError("患者档案不存在")
        return updated

    @staticmethod
    def _to_profile(row) -> Optional[PatientProfile]:
        if not row:
            return None
        return PatientProfile(**row)
