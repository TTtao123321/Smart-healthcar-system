"""敏感词/高危词库 — 可通过配置文件扩展，无需改代码"""

import re

# 医疗诊断类关键词（正则匹配）
DIAGNOSIS_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"诊断",
        r"判断是不是",
        r"治疗方案",
        r"吃什么药",
        r"用什么药",
        r"严重吗",
        r"是不是.*病",
        r"是不是.*(炎|癌|症)",
        r"得了.*病",
        r"有没有.*病",
        r"确诊",
        r"病情怎么样",
        r"怎么治",
        r"能不能治好",
        r"需要手术吗",
        r"需要住院吗",
        r"吃什么药好",
        r"用什么药好",
    ]
]

# 报告解读类关键词（正则匹配）
REPORT_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"指标正常吗",
        r"报告有什么问题",
        r"检查结果怎么样",
        r"化验单怎么看",
        r"血常规.*正常",
        r"CT.*结果",
        r"核磁.*结果",
        r"B超.*结果",
        r"X光.*结果",
        r"报告.*解读",
        r"报告.*分析",
    ]
]

# 高危应急关键词（精确匹配）
EMERGENCY_KEYWORDS: list[str] = [
    "自杀",
    "自残",
    "大出血",
    "呼吸困难",
    "心脏骤停",
    "休克",
    "昏迷",
    "窒息",
    "中毒",
    "溺水",
    "触电",
    "严重外伤",
    "车祸",
    "火灾",
    "胸痛",
    "剧烈头痛",
    "意识丧失",
]

# 边界声明触发词（涉及健康/症状话题时附加免责声明）
HEALTH_TOPIC_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"不舒服",
        r"疼痛",
        r"头晕",
        r"恶心",
        r"发烧",
        r"咳嗽",
        r"拉肚子",
        r"过敏",
        r"失眠",
        r"症状",
        r"感觉.*不对",
        r"身体.*问题",
    ]
]

# 转人工触发条件
HANDOFF_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"投诉",
        r"纠纷",
        r"退款",
        r"赔偿",
        r"不满",
        r"差评",
        r"举报",
        r"我要找.*领导",
        r"我要找.*经理",
        r"转人工",
        r"人工客服",
    ]
]
