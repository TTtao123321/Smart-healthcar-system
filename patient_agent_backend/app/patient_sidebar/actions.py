import json
from typing import Any, Literal

from pydantic import BaseModel, Field


class SidebarActionRequest(BaseModel):
    action: Literal[
        "confirm_registration",
        "view_schedule_change",
        "view_registration_result",
        "view_recent_medical_record",
        "view_recent_prescription",
    ]
    thread_id: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


def build_sidebar_action_message(request: SidebarActionRequest) -> str:
    return json.dumps(
        {
            "source": "patient_sidebar",
            "action": request.action,
            "payload": request.payload,
        },
        ensure_ascii=False,
    )
