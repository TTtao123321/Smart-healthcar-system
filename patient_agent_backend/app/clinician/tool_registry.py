from langchain_core.tools import tool

from app.clinician.models import ClinicianContext
from app.hms_client import HmsClient
from app.tools.clinician_patient_tools import create_clinician_patient_tools
from app.tools.clinician_record_tools import create_clinician_record_tools
from app.tools.tool_response import err


@tool
async def query_patient_medical_records(patient_id: int, limit: int = 3) -> str:
    """查询患者历史病历（临床通道占位实现）。"""
    return err(
        f"临床病历查询能力尚未接入，patient_id={patient_id}，limit={limit}"
    )


_FALLBACK_CLINICIAN_TOOLS = [
    query_patient_medical_records,
    *create_clinician_record_tools(),
]
CLINICIAN_TOOLS: list = []


def init_clinician_tools(hms_client: HmsClient) -> list:
    CLINICIAN_TOOLS.clear()
    CLINICIAN_TOOLS.extend(
        create_clinician_patient_tools(hms_client)
        + create_clinician_record_tools()
    )
    return CLINICIAN_TOOLS


def get_tools_for_channel(
    channel: str,
    context: ClinicianContext | None = None,
) -> list:
    if channel == "clinician":
        return list(CLINICIAN_TOOLS or _FALLBACK_CLINICIAN_TOOLS)
    from app.tools import get_patient_tools

    return list(get_patient_tools())
