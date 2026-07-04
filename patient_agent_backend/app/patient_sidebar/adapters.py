from datetime import date, datetime
from typing import Optional

from app.patient_profile.models import PatientProfile
from app.patient_sidebar.models import (
    SidebarDepartment,
    SidebarDoctor,
    SidebarProfile,
    SidebarRecentVisit,
    SidebarSchedule,
)


def _mask_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_pid(pid: Optional[str]) -> str:
    if not pid:
        return ""
    return pid[-4:]


def _calc_age(birthday: Optional[str]) -> Optional[int]:
    if not birthday:
        return None
    born = datetime.strptime(birthday, "%Y-%m-%d").date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def build_sidebar_profile(profile: PatientProfile) -> SidebarProfile:
    return SidebarProfile(
        patientId=str(profile.id),
        name=profile.name,
        gender=profile.sex,
        age=_calc_age(profile.birthday),
        phone=_mask_phone(profile.tel),
        idCardMasked=_mask_pid(profile.pid),
    )


def build_recent_visits(items: list[dict], limit: int = 3) -> list[SidebarRecentVisit]:
    visits = [
        SidebarRecentVisit(
            visitId=str(item.get("registrationId", item.get("id", ""))),
            visitDate=item.get("date") or "",
            department=item.get("deptSubName") or item.get("deptName") or "--",
            doctorName=item.get("doctorName") or "--",
            hasMedicalRecord=bool(item.get("medicalRecordId")),
            hasPrescription=bool(item.get("hasPrescription")),
            latestResultStatus=item.get("latestResultStatus") or "",
            medicalRecordId=(
                str(item.get("medicalRecordId"))
                if item.get("medicalRecordId") not in (None, "")
                else None
            ),
            prescriptionId=(
                str(item.get("prescriptionId"))
                if item.get("prescriptionId") not in (None, "")
                else None
            ),
        )
        for item in items
    ]
    visits.sort(key=lambda item: item.visitDate, reverse=True)
    return visits[:limit]


def build_sidebar_schedule(date_str: str, departments: list[dict]) -> SidebarSchedule:
    sidebar_departments: list[SidebarDepartment] = []
    for department in departments:
        doctors = [
            SidebarDoctor(
                doctorId=str(doctor.get("doctorId", "")),
                doctorName=doctor.get("doctorName", ""),
                title=doctor.get("title", ""),
                bio=doctor.get("bio", ""),
                departmentName=department.get("departmentName", ""),
                timeSlots=doctor.get("timeSlots", []),
            )
            for doctor in department.get("doctors", [])
        ]
        sidebar_departments.append(
            SidebarDepartment(
                departmentId=str(department.get("departmentId", "")),
                departmentName=department.get("departmentName", ""),
                doctors=doctors,
            )
        )
    return SidebarSchedule(dateLabel=date_str, departments=sidebar_departments)
