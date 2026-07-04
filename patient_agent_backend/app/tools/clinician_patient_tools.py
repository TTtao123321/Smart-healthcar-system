"""临床通道患者历史资料查询工具。"""

from langchain_core.tools import tool

from app.clinician.context import get_clinician_context
from app.clinician.models import ClinicianContext
from app.hms_client import HmsClient
from app.hms_client.models import RegistrationQueryRequest
from app.tools.tool_response import empty, err, ok


def _require_clinician_context() -> ClinicianContext:
    context = get_clinician_context()
    if context is None:
        raise ValueError("临床身份上下文缺失，无法查询患者资料")
    return context


def _is_root_context(context: ClinicianContext) -> bool:
    return any(role.upper() == "ROOT" for role in context.role_codes)


def _is_registration_allowed(context: ClinicianContext, registration) -> bool:
    if _is_root_context(context):
        return True
    dept_allowed = (
        not context.dept_scope
        or registration.dept_sub_id in context.dept_scope
    )
    doctor_allowed = (
        not context.doctor_scope
        or registration.doctor_id in context.doctor_scope
    )
    if not context.dept_scope and not context.doctor_scope:
        return False
    return dept_allowed and doctor_allowed


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


async def _allowed_registration_ids(
    hms_client: HmsClient,
    context: ClinicianContext,
    patient_id: int,
) -> set[int] | None:
    if _is_root_context(context):
        return None
    registrations = await hms_client.registration_service.query(
        RegistrationQueryRequest(patient_id=patient_id)
    )
    return {
        item.id
        for item in registrations.items
        if _is_registration_allowed(context, item)
    }


def create_clinician_patient_tools(hms_client: HmsClient):
    @tool
    async def search_patient_profiles(
        name: str,
        phone_suffix: str | None = None,
    ) -> str:
        """按姓名搜索患者，必要时用手机号后四位缩小范围。"""
        try:
            _require_clinician_context()
            data = await hms_client.post(
                "/patient/selectByPage",
                json={"page": 1, "length": 10, "name": name},
            )
        except ValueError as exc:
            return err(str(exc))
        except Exception as exc:
            return err(f"查询患者失败: {exc}")

        result = data.get("result", data)
        items = result.get("list", []) if isinstance(result, dict) else []
        profiles = []
        for item in items:
            phone = item.get("tel") or item.get("phone") or ""
            if phone_suffix and not str(phone).endswith(str(phone_suffix)):
                continue
            profiles.append(
                {
                    "patientId": item.get("patientId", item.get("id")),
                    "name": item.get("name"),
                    "sex": item.get("sex"),
                    "phoneMasked": _mask_phone(str(phone) if phone else ""),
                }
            )
        if not profiles:
            return empty("未找到匹配患者")
        return ok("已查询到匹配患者", profiles)

    @tool
    async def query_patient_medical_records(patient_id: int, limit: int = 3) -> str:
        """按患者 ID 查询授权范围内的历史病历列表。"""
        try:
            context = _require_clinician_context()
            allowed_registration_ids = await _allowed_registration_ids(
                hms_client,
                context,
                patient_id,
            )
            result = await hms_client.medical_record_service.query_patient_records(
                patient_id=patient_id,
            )
        except ValueError as exc:
            return err(str(exc))
        except Exception as exc:
            return err(f"查询患者历史病历失败: {exc}")

        records = [
            item.model_dump()
            for item in result.items
            if allowed_registration_ids is None
            or item.registrationId in allowed_registration_ids
        ][:limit]
        if not records:
            return empty("授权范围内暂无患者历史病历")
        return ok("已查询到患者历史病历", records)

    @tool
    async def get_patient_medical_record_detail(
        patient_id: int,
        medical_record_id: int,
    ) -> str:
        """按患者 ID 和病历 ID 查询授权范围内的病历详情。"""
        try:
            context = _require_clinician_context()
            allowed_registration_ids = await _allowed_registration_ids(
                hms_client,
                context,
                patient_id,
            )
            detail = await hms_client.medical_record_service.get_detail(
                patient_id,
                medical_record_id,
            )
        except ValueError as exc:
            return err(str(exc))
        except Exception as exc:
            return err(f"查询患者病历详情失败: {exc}")

        if (
            allowed_registration_ids is not None
            and detail.registrationId not in allowed_registration_ids
        ):
            return err("无权查看该患者病历详情")
        return ok("已查询到患者病历详情", detail.model_dump())

    return [
        search_patient_profiles,
        query_patient_medical_records,
        get_patient_medical_record_detail,
    ]
