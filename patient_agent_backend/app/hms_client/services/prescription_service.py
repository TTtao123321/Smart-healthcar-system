"""患者处方服务 — 对接 HMS 患者处方查询 API"""

from typing import TYPE_CHECKING

from app.hms_client.models import (
    PrescriptionDetailItem,
    PrescriptionDetailResponse,
    PrescriptionListItem,
    PrescriptionListResponse,
)

if TYPE_CHECKING:
    from app.hms_client.client import HmsClient


class PrescriptionService:
    def __init__(self, client: "HmsClient"):
        self._client = client

    async def query_patient_prescriptions(
        self,
        patient_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> PrescriptionListResponse:
        data = await self._client.post(
            "/patient/prescriptions",
            json={
                "patientId": patient_id,
                **({"startDate": start_date} if start_date else {}),
                **({"endDate": end_date} if end_date else {}),
            },
        )
        result = data.get("result", data)
        return PrescriptionListResponse(
            items=[PrescriptionListItem(**item) for item in result]
        )

    async def get_detail(self, patient_id: int, prescription_id: int) -> PrescriptionDetailResponse:
        data = await self._client.post(
            "/patient/prescriptions/detail",
            json={"patientId": patient_id, "prescriptionId": prescription_id},
        )
        result = data.get("result", data)
        items = result.get("items", [])
        result = {**result, "items": [PrescriptionDetailItem(**item) for item in items]}
        return PrescriptionDetailResponse(**result)
