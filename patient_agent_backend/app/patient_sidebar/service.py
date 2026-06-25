from fastapi import HTTPException

from app.patient_sidebar.adapters import (
    build_recent_visits,
    build_sidebar_profile,
    build_sidebar_schedule,
)
from app.patient_sidebar.models import SidebarResponse


class PatientSidebarService:
    def __init__(self, profile_service, registration_service, schedule_gateway):
        self._profile_service = profile_service
        self._registration_service = registration_service
        self._schedule_gateway = schedule_gateway

    async def get_sidebar(self, patient_id: int) -> SidebarResponse:
        profile = await self._profile_service.get_by_id(patient_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="患者档案不存在")

        recent_visits = []
        try:
            visit_items = await self._registration_service.query_recent(patient_id, limit=3)
            recent_visits = build_recent_visits(visit_items, limit=3)
        except Exception:
            recent_visits = []

        schedule_payload = {"dateLabel": "", "departments": []}
        try:
            schedule_payload = await self._schedule_gateway.get_today_schedule()
        except Exception:
            schedule_payload = {"dateLabel": "", "departments": []}

        return SidebarResponse(
            profile=build_sidebar_profile(profile),
            recentVisits=recent_visits,
            schedule=build_sidebar_schedule(
                schedule_payload.get("dateLabel", ""),
                schedule_payload.get("departments", []),
            ),
        )
