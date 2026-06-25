from typing import Optional
from pydantic import BaseModel, ConfigDict


class PatientProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    name: str
    sex: Optional[str] = None
    pid: Optional[str] = None
    tel: str
    birthday: Optional[str] = None
    insurance_type: Optional[int] = None
    medical_history: Optional[str] = None
    allergy_history: Optional[str] = None
    family_history: Optional[str] = None


class PatientProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    sex: Optional[str] = None
    pid: Optional[str] = None
    birthday: Optional[str] = None
    insurance_type: Optional[int] = None
    medical_history: Optional[str] = None
    allergy_history: Optional[str] = None
    family_history: Optional[str] = None
