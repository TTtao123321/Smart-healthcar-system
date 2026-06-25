from pydantic import BaseModel


class PatientSession(BaseModel):
    token: str
    patient_id: int
    phone: str
    name: str
    login_time: str
