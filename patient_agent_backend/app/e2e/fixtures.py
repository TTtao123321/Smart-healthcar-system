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
        "dateLabel": "2026年6月28日 周日",
        "departments": [
            {
                "departmentId": "dept-cardiology",
                "departmentName": "心内科",
                "doctors": [
                    {
                        "doctorId": "doctor-003",
                        "doctorName": "张医生",
                        "title": "主任医师",
                        "bio": "擅长心血管疾病诊疗与慢病管理",
                        "departmentName": "心内科",
                        "timeSlots": ["08:00-12:00", "14:00-17:00"],
                        "workPlanId": 11,
                    },
                ],
            }
        ],
    },
}
