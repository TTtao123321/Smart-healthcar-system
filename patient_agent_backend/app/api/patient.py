from fastapi import APIRouter, Depends, HTTPException

from app.api.chat import get_orchestrator
from app.auth.dependencies import require_patient_session
from app.auth.models import PatientSession
from app.api.auth import get_patient_profile_service, get_patient_sidebar_service
from app.config.settings import settings
from app.e2e.service import get_e2e_service
from app.patient_sidebar.actions import SidebarActionRequest, build_sidebar_action_message
from app.patient_profile.models import PatientProfileUpdate

router = APIRouter(prefix="/api/patient", tags=["患者档案"])


@router.get("/profile")
async def get_profile(session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return get_e2e_service().get_profile(session.patient_id)

    profile = await get_patient_profile_service().get_by_id(session.patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    return profile.model_dump()


@router.get("/sidebar")
async def get_sidebar(session: PatientSession = Depends(require_patient_session)):
    if settings.patient_agent_e2e_mode:
        return get_e2e_service().get_sidebar(session.patient_id)

    sidebar = await get_patient_sidebar_service().get_sidebar(session.patient_id)
    return sidebar.model_dump()


@router.post("/sidebar/action")
async def sidebar_action(
    payload: SidebarActionRequest,
    session: PatientSession = Depends(require_patient_session),
):
    if settings.patient_agent_e2e_mode:
        raw_payload = payload.payload.model_dump() if hasattr(payload.payload, "model_dump") else payload.payload
        return get_e2e_service().run_sidebar_action(
            patient_id=session.patient_id,
            action=payload.action,
            thread_id=payload.thread_id,
            payload=raw_payload,
        )

    result = await get_orchestrator().run_once(
        session=session,
        user_message=build_sidebar_action_message(payload),
        thread_id=payload.thread_id,
    )
    return {
        "message": result.message,
        "thread_id": result.thread_id,
        "needs_handoff": result.needs_handoff,
        "reply_type": result.reply_type,
        "degraded": result.degraded,
    }


@router.post("/profile")
async def update_profile(
    payload: PatientProfileUpdate,
    session: PatientSession = Depends(require_patient_session),
):
    profile = await get_patient_profile_service().update_profile(session.patient_id, payload)
    return profile.model_dump()
