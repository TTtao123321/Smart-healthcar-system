from contextvars import ContextVar

from app.clinician.models import ClinicianContext

current_clinician_context: ContextVar[ClinicianContext | None] = ContextVar(
    "current_clinician_context",
    default=None,
)


def set_clinician_context(context: ClinicianContext | None) -> None:
    current_clinician_context.set(context)


def get_clinician_context() -> ClinicianContext | None:
    return current_clinician_context.get()
