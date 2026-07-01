import pytest


@pytest.mark.asyncio
async def test_consumer_saves_schedule_suspended_notification():
    from app.notifications.consumer import NotificationConsumer
    from app.notifications.repository import InMemoryNotificationRepository

    repo = InMemoryNotificationRepository()
    consumer = NotificationConsumer(repository=repo)

    event = {
        "eventId": "evt-1",
        "eventType": "schedule.suspended",
        "payload": {
            "workPlanId": 12,
            "affectedPatientIds": [88],
        },
    }

    await consumer.handle_event(event)

    items = await repo.list_recent(88, limit=5)
    assert items[0].kind == "schedule_suspended"
    assert items[0].title == "停诊提醒"
