from pydantic import BaseModel, Field


class ClinicianContext(BaseModel):
    user_id: int
    role_codes: list[str] = Field(default_factory=list)
    dept_scope: list[int] = Field(default_factory=list)
    doctor_scope: list[int] = Field(default_factory=list)
