from pydantic import BaseModel


class NotificationItem(BaseModel):
    eventId: str
    kind: str
    title: str
    body: str
