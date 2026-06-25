from app.patient_profile.models import PatientProfile, PatientProfileUpdate
from app.patient_profile.service import PatientProfileService


class FakeRepository:
    def __init__(self):
        self.by_phone = {}
        self.by_id = {}
        self.next_id = 1

    async def get_by_phone(self, phone: str):
        return self.by_phone.get(phone)

    async def get_by_id(self, patient_id: int):
        return self.by_id.get(patient_id)

    async def create_patient(self, profile: PatientProfile):
        created = profile.model_copy(update={"id": self.next_id})
        self.next_id += 1
        self.by_phone[created.tel] = created
        self.by_id[created.id] = created
        return created

    async def update_patient_basic_info(self, patient_id: int, payload: PatientProfileUpdate):
        current = self.by_id[patient_id]
        updated = current.model_copy(update=payload.model_dump(exclude_unset=True))
        self.by_id[patient_id] = updated
        self.by_phone[updated.tel] = updated
        return updated


async def test_get_or_create_by_phone_creates_new_patient():
    repo = FakeRepository()
    service = PatientProfileService(repo)

    profile = await service.get_or_create_by_phone("13800138000")

    assert profile.id > 0
    assert profile.tel == "13800138000"
    assert profile.name == "患者8000"


async def test_update_profile_updates_allowed_fields_only():
    repo = FakeRepository()
    repo.by_id[7] = PatientProfile(id=7, uuid="u7", name="患者8000", tel="13800138000")
    service = PatientProfileService(repo)

    updated = await service.update_profile(7, PatientProfileUpdate(name="张三", sex="男"))

    assert updated.id == 7
    assert updated.tel == "13800138000"
    assert updated.name == "张三"
    assert updated.sex == "男"
