import logging

from app.agent.request_context import get_patient_id, get_thread_id
from app.middleware.request_context import get_request_id


class RequestContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = dict(kwargs.get("extra") or {})
        extra.setdefault("request_id", get_request_id())
        extra.setdefault("patient_id", get_patient_id())
        extra.setdefault("thread_id", get_thread_id())
        kwargs["extra"] = extra
        return msg, kwargs


def get_request_logger(name: str) -> RequestContextLoggerAdapter:
    return RequestContextLoggerAdapter(logging.getLogger(name), {})


def log_chat_result(
    logger: RequestContextLoggerAdapter,
    *,
    guardrail_result: str | None,
    reply_type: str,
    degraded: bool,
) -> None:
    logger.info(
        "chat_result",
        extra={
            "guardrail_result": guardrail_result,
            "reply_type": reply_type,
            "degraded": degraded,
        },
    )
