"""患者病历服务 — 对接 HMS 患者病历查询 API"""

from typing import TYPE_CHECKING

from app.hms_client.models import (
    MedicalRecordDetailResponse,
    MedicalRecordListItem,
    MedicalRecordListResponse,
)

if TYPE_CHECKING:
    from app.hms_client.client import HmsClient


class MedicalRecordService:
    def __init__(self, client: "HmsClient"):
        self._client = client

    async def query_patient_records(
        self,
        patient_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> MedicalRecordListResponse:
        data = await self._client.post(
            "/patient/medical-records",
            json={
                "patientId": patient_id,
                **({"startDate": start_date} if start_date else {}),
                **({"endDate": end_date} if end_date else {}),
            },
        )
        result = data.get("result", data)
        return MedicalRecordListResponse(
            items=[MedicalRecordListItem(**item) for item in result]
        )

    async def get_detail(self, patient_id: int, medical_record_id: int) -> MedicalRecordDetailResponse:
        data = await self._client.post(
            "/patient/medical-records/detail",
            json={"patientId": patient_id, "medicalRecordId": medical_record_id},
        )
        result = data.get("result", data)
        return MedicalRecordDetailResponse(**result)
