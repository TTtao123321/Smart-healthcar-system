"""输出安全护栏 — 检查 LLM 响应是否含医疗建议，附加免责声明"""

import re

# 医疗建议性输出检测模式
MEDICAL_ADVICE_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"建议你(吃|服用|使用).*(药|片|胶囊)",
        r"你应该.*治疗",
        r"你可以.*自行.*用药",
        r"不需要.*就医",
        r"不用.*看医生",
        r"这个(病|症状).*不严重",
    ]
]

# 疑似编造内容检测模式
HALLUCINATION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"医院地址[：:]\s*\S",       # 编造地址
        r"位于\S+路",                 # 编造具体位置
        r"联系电话[：:]\s*\d",        # 编造电话
        r"擅长\S{2,}(治疗|手术|诊断)",  # 编造医生擅长领域（非工具返回）
        r"毕业于\S+",                 # 编造医生毕业院校
        r"从事\S+年",                 # 编造医生从业年限
    ]
]

DISCLAIMER = "⚠️ 以上信息仅供参考，不能替代医生面诊。如有身体不适，请尽快到院就诊。"

HALLUCINATION_WARNING = (
    "【系统提示】以下回复可能包含未经核实的信息，请以医院官方数据为准。"
    "如需准确信息，请咨询医院工作人员。\n"
)


def check_output(
    assistant_message: str,
    needs_disclaimer: bool = False,
    disclaimer_shown: bool = False,
) -> tuple[str, bool]:
    """对 LLM 输出进行安全检查

    Args:
        assistant_message: LLM 生成的回复
        needs_disclaimer: 是否需要附加免责声明（由输入护栏标记）
        disclaimer_shown: 是否已展示过免责声明

    Returns:
        (processed_message, disclaimer_shown): 处理后的消息和免责声明状态
    """
    message = assistant_message
    should_show_disclaimer = False

    # 1. 检查是否包含医疗建议性内容
    for pattern in MEDICAL_ADVICE_PATTERNS:
        if pattern.search(message):
            # 在医疗建议前插入警告
            message = (
                "【系统提示：以下内容可能包含医疗建议，请以医生意见为准】\n"
                + message
            )
            should_show_disclaimer = True
            break

    # 2. 检查是否包含疑似编造内容
    for pattern in HALLUCINATION_PATTERNS:
        if pattern.search(message):
            # 在编造内容前插入警告
            message = HALLUCINATION_WARNING + message
            should_show_disclaimer = True
            break

    # 3. 判断是否需要附加免责声明
    if needs_disclaimer and not disclaimer_shown:
        should_show_disclaimer = True

    if should_show_disclaimer:
        message = message.rstrip() + "\n\n" + DISCLAIMER
        disclaimer_shown = True

    return message, disclaimer_shown
