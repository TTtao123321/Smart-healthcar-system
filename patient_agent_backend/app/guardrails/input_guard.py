"""输入安全护栏 — 敏感词拦截、高危识别、边界声明"""

from dataclasses import dataclass

from app.guardrails.keywords import (
    DIAGNOSIS_PATTERNS,
    REPORT_PATTERNS,
    EMERGENCY_KEYWORDS,
    HEALTH_TOPIC_PATTERNS,
    HANDOFF_PATTERNS,
)


@dataclass
class GuardrailResult:
    """护栏检查结果"""
    blocked: bool = False
    reason: str = ""
    response: str = ""
    needs_handoff: bool = False
    needs_disclaimer: bool = False


def check_input(user_message: str) -> GuardrailResult:
    """对用户输入进行安全检查

    检查优先级：高危应急 > 医疗诊断 > 报告解读 > 转人工 > 边界声明
    """
    result = GuardrailResult()

    # 1. 高危应急检查（最高优先级）
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in user_message:
            result.blocked = True
            result.needs_handoff = True
            result.reason = "high_emergency"
            result.response = (
                "⚠️ 您描述的情况属于紧急医疗状况，请立即拨打120急救电话或前往最近的急诊科！\n"
                "如需心理危机援助，请拨打24小时心理援助热线：400-161-9995\n"
                "我将为您转接人工客服。"
            )
            return result

    # 2. 医疗诊断拦截
    for pattern in DIAGNOSIS_PATTERNS:
        if pattern.search(user_message):
            result.blocked = True
            result.reason = "diagnosis_request"
            result.response = (
                "抱歉，我无法提供疾病诊断或治疗建议。"
                "我的职责是帮助您查询科室、医生排班和挂号等就医流程信息。"
                "如需医疗建议，请直接咨询医生。"
            )
            return result

    # 3. 报告解读拦截
    for pattern in REPORT_PATTERNS:
        if pattern.search(user_message):
            result.blocked = True
            result.reason = "report_interpretation"
            result.response = (
                "抱歉，我无法解读医疗报告或检查结果。"
                "请携带您的检查报告咨询主治医生，医生会为您详细解读。"
            )
            return result

    # 4. 转人工触发
    for pattern in HANDOFF_PATTERNS:
        if pattern.search(user_message):
            result.needs_handoff = True
            result.reason = "handoff_request"
            result.response = "好的，我将为您转接人工客服，请稍候。"
            return result

    # 5. 边界声明（不拦截，仅标记需要附加免责声明）
    for pattern in HEALTH_TOPIC_PATTERNS:
        if pattern.search(user_message):
            result.needs_disclaimer = True
            result.reason = "health_topic"
            break

    return result
