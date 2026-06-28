BASELINE_THREADS = [
    {
        "thread_id": "thread-1",
        "title": "历史对话一",
        "last_message": "这是历史消息",
        "updated_at": "2026-06-27T14:00:00",
    }
]

BASELINE_HISTORY = {
    "thread-1": [
        {"role": "user", "content": "这是历史消息"},
        {"role": "assistant", "content": "继续为您处理。"},
    ]
}

BASELINE_SIDEBAR = {
    "profile": {
        "id": 12,
        "name": "张三",
        "gender": "男",
        "age": 32,
        "recentVisits": [],
    },
    "recentVisits": [],
    "schedule": {
        "dateLabel": "2026-06-28",
        "departments": [
            {
                "departmentName": "心内科",
                "doctors": [
                    {"doctorId": 3, "doctorName": "张医生", "workPlanId": 11},
                ],
            }
        ],
    },
}
