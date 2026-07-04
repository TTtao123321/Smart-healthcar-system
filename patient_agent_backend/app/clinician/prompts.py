from app.agent.prompts import build_patient_system_prompt
from app.clinician.models import ClinicianContext


def build_clinician_system_prompt(context: ClinicianContext) -> str:
    role_codes = "、".join(context.role_codes) if context.role_codes else "未分配角色"
    dept_scope = "、".join(str(item) for item in context.dept_scope) or "无科室范围"
    doctor_scope = "、".join(str(item) for item in context.doctor_scope) or "无医生范围"
    return (
        "你是XX医院医生工作助手，服务对象为院内医护人员。\n"
        "仅可在授权范围内帮助医生查询患者历史资料和生成病历草稿。\n"
        "所有 AI 草稿都必须标记为“AI 草稿，仅供医生审核”，不得直接落库。\n"
        f"当前角色: {role_codes}\n"
        f"科室范围: {dept_scope}\n"
        f"医生范围: {doctor_scope}\n\n"
        f"{build_patient_system_prompt()}"
    )
