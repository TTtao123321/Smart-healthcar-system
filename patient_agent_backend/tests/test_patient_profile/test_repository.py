from app.patient_profile.models import PatientProfile
from app.patient_profile.repository import PatientProfileRepository


class FakeCursor:
    def __init__(self, fetchone_result=None, lastrowid=0):
        self.fetchone_result = fetchone_result
        self.lastrowid = lastrowid
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def execute(self, sql, params):
        self.executed.append((sql, params))

    async def fetchone(self):
        return self.fetchone_result


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def cursor(self, *_args, **_kwargs):
        return self._cursor


class FakePool:
    def __init__(self, cursor):
        self._cursor = cursor

    def acquire(self):
        return FakeConnection(self._cursor)


async def test_get_by_phone_maps_database_row():
    cursor = FakeCursor(
        fetchone_result={
            "id": 5,
            "uuid": "u5",
            "name": "张三",
            "sex": "男",
            "pid": "110101199001011234",
            "tel": "13800138000",
            "birthday": "1990-01-01",
            "insurance_type": 1,
            "medical_history": "无",
            "allergy_history": "无",
            "family_history": "无",
        }
    )
    repo = PatientProfileRepository(FakePool(cursor))

    profile = await repo.get_by_phone("13800138000")

    assert profile is not None
    assert profile.id == 5
    assert profile.name == "张三"
    assert profile.tel == "13800138000"


async def test_create_patient_returns_profile_with_generated_id():
    cursor = FakeCursor(lastrowid=8)
    repo = PatientProfileRepository(FakePool(cursor))

    created = await repo.create_patient(
        PatientProfile(id=0, uuid="u8", name="患者8000", tel="13800138000")
    )

    assert created.id == 8
    assert created.tel == "13800138000"
    assert cursor.executed
