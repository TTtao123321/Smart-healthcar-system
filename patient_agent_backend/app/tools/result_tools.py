"""病历/处方查询工具"""

from langchain_core.tools import tool

from app.agent.request_context import get_patient_id
from app.hms_client import HmsClient
from app.tools.tool_response import empty, err, ok


def _require_session_patient_id() -> int:
    patient_id = get_patient_id()
    if patient_id is None:
        raise ValueError("请先登录后再查询病历或处方")
    return int(patient_id)


def create_result_tools(hms_client: HmsClient):
    @tool
    async def query_my_medical_records(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """查询当前登录患者的病历列表。"""
        try:
            patient_id = _require_session_patient_id()
            result = await hms_client.medical_record_service.query_patient_records(
                patient_id=patient_id,
                start_date=start_date,
                end_date=end_date,
            )
        except ValueError as e:
            return err(str(e))
        except Exception as e:
            return err(f"查询病历失败: {e}")

        if not result.items:
            return empty("暂无病历记录")
        return ok("已查询到病历记录", [item.model_dump() for item in result.items])

    @tool
    async def get_medical_record_detail(medical_record_id: int) -> str:
        """查询当前登录患者的病历详情。"""
        try:
            patient_id = _require_session_patient_id()
            result = await hms_client.medical_record_service.get_detail(patient_id, medical_record_id)
        except ValueError as e:
            return err(str(e))
        except Exception as e:
            return err(f"查询病历详情失败: {e}")
        return ok("已查询到病历详情", result.model_dump())

    @tool
    async def query_my_prescriptions(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """查询当前登录患者的处方列表。"""
        try:
            patient_id = _require_session_patient_id()
            result = await hms_client.prescription_service.query_patient_prescriptions(
                patient_id=patient_id,
                start_date=start_date,
                end_date=end_date,
            )
        except ValueError as e:
            return err(str(e))
        except Exception as e:
            return err(f"查询处方失败: {e}")

        if not result.items:
            return empty("暂无处方记录")
        return ok("已查询到处方记录", [item.model_dump() for item in result.items])

    @tool
    async def get_prescription_detail(prescription_id: int) -> str:
        """查询当前登录患者的处方详情。"""
        try:
            patient_id = _require_session_patient_id()
            result = await hms_client.prescription_service.get_detail(patient_id, prescription_id)
        except ValueError as e:
            return err(str(e))
        except Exception as e:
            return err(f"查询处方详情失败: {e}")
        return ok("已查询到处方详情", result.model_dump())

    return [
        query_my_medical_records,
        get_medical_record_detail,
        query_my_prescriptions,
        get_prescription_detail,
    ]
