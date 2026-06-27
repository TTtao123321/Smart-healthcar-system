from datetime import date

from app.hms_client.models import ScheduleListRequest


def _format_date_label(current_date: date) -> str:
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return f"{current_date.year}年{current_date.month}月{current_date.day}日 {weekday_map[current_date.weekday()]}"


def _slot_to_time_range(slot: int) -> str:
    if isinstance(slot, list):
        labels = []
        if any(slot[:8]):
            labels.append("08:00-12:00")
        if any(slot[8:]):
            labels.append("14:00-17:30")
        return " / ".join(labels)
    if slot <= 0:
        return ""
    if slot <= 8:
        return "08:00-12:00"
    return "14:00-17:30"


class PatientScheduleGateway:
    def __init__(self, dept_service, doctor_service):
        self._dept_service = dept_service
        self._doctor_service = doctor_service

    async def get_today_schedule(self) -> dict:
        current_date = date.today()
        current_date_str = current_date.isoformat()
        departments = []

        for department in await self._dept_service.list_all_names():
            doctors = []
            for sub_dept in await self._dept_service.list_sub_depts(department.id):
                doctor_items = await self._doctor_service.list_by_sub_dept(sub_dept.id)
                schedule_items = await self._doctor_service.schedules(
                    ScheduleListRequest(dept_sub_id=sub_dept.id, date=current_date_str)
                )

                schedule_map = {}
                for item in schedule_items.items:
                    doctor_id = item.get("doctorId")
                    if not doctor_id:
                        continue
                    slot_label = _slot_to_time_range(item.get("slot", 0))
                    if not slot_label:
                        continue
                    schedule_map.setdefault(str(doctor_id), [])
                    if slot_label not in schedule_map[str(doctor_id)]:
                        schedule_map[str(doctor_id)].append(slot_label)

                for doctor in doctor_items:
                    time_slots = schedule_map.get(str(doctor.id), [])
                    if not time_slots:
                        continue
                    doctors.append({
                        "doctorId": str(doctor.id),
                        "doctorName": doctor.name,
                        "title": doctor.job or "",
                        "bio": doctor.description or "",
                        "timeSlots": time_slots,
                    })

            departments.append({
                "departmentId": str(department.id),
                "departmentName": department.name,
                "doctors": doctors,
            })

        return {
            "dateLabel": _format_date_label(current_date),
            "departments": departments,
        }
