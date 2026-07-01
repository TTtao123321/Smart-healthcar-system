import json
import logging
from typing import Any

from app.config.settings import settings
from app.notifications.models import NotificationItem

logger = logging.getLogger(__name__)


class NotificationConsumer:
    ROUTE_KEYS = (
        "registration.created",
        "registration.cancelled",
        "schedule.updated",
        "schedule.suspended",
    )

    def __init__(self, repository):
        self._repository = repository
        self._connection = None
        self._channel = None
        self._queue = None

    async def start(self) -> None:
        try:
            import aio_pika
        except ImportError:
            logger.warning("aio-pika 未安装，跳过通知消费者启动")
            return

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        exchange = await self._channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self._queue = await self._channel.declare_queue(settings.rabbitmq_notifications_queue, durable=True)
        for route_key in self.ROUTE_KEYS:
            await self._queue.bind(exchange, routing_key=route_key)
        await self._queue.consume(self._on_message)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()

    async def _on_message(self, message) -> None:
        async with message.process():
            payload = json.loads(message.body.decode("utf-8"))
            await self.handle_event(payload)

    async def handle_event(self, event: dict[str, Any]) -> None:
        event_id = str(event.get("eventId") or "")
        if not event_id:
            return
        if not await self._repository.mark_processed(event_id):
            return

        event_type = event.get("eventType") or ""
        payload = event.get("payload") or {}
        for patient_id, item in self._build_notifications(event_id, event_type, payload):
            await self._repository.save(patient_id, item)

    def _build_notifications(
        self, event_id: str, event_type: str, payload: dict[str, Any]
    ) -> list[tuple[int, NotificationItem]]:
        if event_type == "registration.created":
            patient_id = int(payload.get("patientId") or 0)
            if not patient_id:
                return []
            return [(
                patient_id,
                NotificationItem(
                    eventId=event_id,
                    kind="registration_created",
                    title="挂号成功提醒",
                    body="您的挂号已成功，侧栏可查看最新排班信息。",
                ),
            )]

        if event_type == "registration.cancelled":
            patient_id = int(payload.get("patientId") or 0)
            if not patient_id:
                return []
            return [(
                patient_id,
                NotificationItem(
                    eventId=event_id,
                    kind="registration_cancelled",
                    title="挂号取消提醒",
                    body="您的挂号已取消，号源库存已自动回补。",
                ),
            )]

        if event_type in {"schedule.updated", "schedule.suspended"}:
            patient_ids = payload.get("affectedPatientIds") or []
            title = "排班调整提醒" if event_type == "schedule.updated" else "停诊提醒"
            body = "您已挂号的排班发生调整，请重新确认出诊安排。" if event_type == "schedule.updated" else "您已挂号的排班已停诊，请重新查询并改约。"
            kind = "schedule_updated" if event_type == "schedule.updated" else "schedule_suspended"
            return [
                (
                    int(patient_id),
                    NotificationItem(
                        eventId=event_id,
                        kind=kind,
                        title=title,
                        body=body,
                    ),
                )
                for patient_id in patient_ids
                if patient_id
            ]

        return []
