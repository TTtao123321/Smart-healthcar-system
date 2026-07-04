"""医护端 Agent 聊天接口。"""

from types import SimpleNamespace
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.agent.graph import compile_graph
from app.api.chat import get_memory
from app.auth.clinician_dependencies import require_clinician_context
from app.chat.orchestrator import ChatOrchestrator
from app.clinician.models import ClinicianContext

router = APIRouter(prefix="/api/clinician", tags=["医护助手"])


class ClinicianChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1)
    thread_id: str | None = Field(default=None, alias="threadId")
    user_id: int = Field(alias="userId")
    role_codes: list[str] = Field(default_factory=list, alias="roleCodes")
    dept_scope: list[int] = Field(default_factory=list, alias="deptScope")
    doctor_scope: list[int] = Field(default_factory=list, alias="doctorScope")


@router.post("/chat")
async def clinician_chat(request: ClinicianChatRequest):
    context = require_clinician_context(
        ClinicianContext(
            user_id=request.user_id,
            role_codes=request.role_codes,
            dept_scope=request.dept_scope,
            doctor_scope=request.doctor_scope,
        )
    )
    thread_id = request.thread_id or str(uuid4())
    session = SimpleNamespace(
        patient_id=context.user_id,
        token=f"clinician:{context.user_id}",
        name=f"clinician:{context.user_id}",
        phone="",
    )
    result = await ChatOrchestrator(
        memory=get_memory(),
        graph_factory=compile_graph,
        channel="clinician",
        clinician_context=context,
    ).run_once(
        session=session,
        user_message=request.message,
        thread_id=thread_id,
    )
    return {
        "channel": "clinician",
        "message": result.message,
        "thread_id": result.thread_id,
        "needs_handoff": result.needs_handoff,
        "reply_type": result.reply_type,
        "degraded": result.degraded,
    }
