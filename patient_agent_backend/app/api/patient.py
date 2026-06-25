from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_patient_session
from app.auth.models import PatientSession
from app.api.auth import get_patient_profile_service, get_patient_sidebar_service
from app.patient_profile.models import PatientProfileUpdate

router = APIRouter(prefix="/api/patient", tags=["患者档案"])


@router.get("/profile")
async def get_profile(session: PatientSession = Depends(require_patient_session)):
    profile = await get_patient_profile_service().get_by_id(session.patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    return profile.model_dump()


@router.get("/sidebar")
async def get_sidebar(session: PatientSession = Depends(require_patient_session)):
    sidebar = await get_patient_sidebar_service().get_sidebar(session.patient_id)
    return sidebar.model_dump()


@router.post("/profile")
async def update_profile(
    payload: PatientProfileUpdate,
    session: PatientSession = Depends(require_patient_session),
):
    profile = await get_patient_profile_service().update_profile(session.patient_id, payload)
    return profile.model_dump()
