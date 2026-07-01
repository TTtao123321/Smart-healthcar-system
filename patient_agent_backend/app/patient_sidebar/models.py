from typing import Optional

from pydantic import BaseModel, Field

from app.notifications.models import NotificationItem


class SidebarProfile(BaseModel):
    patientId: str
    name: str
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: str
    idCardMasked: str = ""


class SidebarRecentVisit(BaseModel):
    visitId: str
    visitDate: str
    department: str
    doctorName: str


class SidebarDoctor(BaseModel):
    doctorId: str
    doctorName: str
    title: str = ""
    bio: str = ""
    departmentName: str
    timeSlots: list[str] = Field(default_factory=list)


class SidebarDepartment(BaseModel):
    departmentId: str
    departmentName: str
    doctors: list[SidebarDoctor] = Field(default_factory=list)


class SidebarSchedule(BaseModel):
    dateLabel: str
    departments: list[SidebarDepartment] = Field(default_factory=list)


class SidebarResponse(BaseModel):
    profile: SidebarProfile
    recentVisits: list[SidebarRecentVisit] = Field(default_factory=list)
    schedule: SidebarSchedule
    notifications: list[NotificationItem] = Field(default_factory=list)
