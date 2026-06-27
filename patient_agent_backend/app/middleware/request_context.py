import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware


current_request_id: ContextVar[str | None] = ContextVar("current_request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    current_request_id.set(request_id)


def get_request_id() -> str | None:
    return current_request_id.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
