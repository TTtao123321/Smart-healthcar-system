from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.settings import settings
from app.e2e.service import get_e2e_service

router = APIRouter(prefix="/api/e2e", tags=["E2E"])


class ResetRequest(BaseModel):
    scenario: str = "baseline"


@router.get("/status")
async def status():
    if not settings.patient_agent_e2e_mode:
        raise HTTPException(status_code=404, detail="E2E mode disabled")
    return get_e2e_service().status()


@router.post("/reset")
async def reset(payload: ResetRequest):
    if not settings.patient_agent_e2e_mode:
        raise HTTPException(status_code=404, detail="E2E mode disabled")
    return get_e2e_service().reset(payload.scenario)
