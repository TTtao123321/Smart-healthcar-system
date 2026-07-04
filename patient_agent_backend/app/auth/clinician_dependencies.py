from fastapi import HTTPException

from app.clinician.models import ClinicianContext


def require_clinician_context(context: ClinicianContext) -> ClinicianContext:
    if context.user_id <= 0:
        raise HTTPException(status_code=400, detail="userId 无效")
    if not context.role_codes:
        raise HTTPException(status_code=400, detail="roleCodes 不能为空")
    return context
