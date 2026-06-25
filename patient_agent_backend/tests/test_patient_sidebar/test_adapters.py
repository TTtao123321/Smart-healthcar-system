from app.patient_profile.models import PatientProfile
from app.patient_sidebar.adapters import build_recent_visits, build_sidebar_profile


def test_build_sidebar_profile_masks_phone_and_pid():
    profile = PatientProfile(
        id=123,
        uuid="u1",
        name="张三",
        sex="男",
        pid="110101199001011234",
        tel="13812341024",
        birthday="1990-01-01",
        insurance_type=None,
        medical_history=None,
        allergy_history=None,
        family_history=None,
    )

    result = build_sidebar_profile(profile)

    assert result.patientId == "123"
    assert result.phone == "138****1024"
    assert result.idCardMasked == "1234"
    assert result.age is not None


def test_build_recent_visits_sorts_and_limits_items():
    items = [
        {"registrationId": 1, "date": "2026-06-01", "deptSubName": "内科门诊", "doctorName": "医生A"},
        {"registrationId": 2, "date": "2026-06-18", "deptSubName": "呼吸内科", "doctorName": "医生B"},
        {"registrationId": 3, "date": "2026-06-12", "deptSubName": "消化内科", "doctorName": "医生C"},
        {"registrationId": 4, "date": "2026-06-20", "deptSubName": "外科门诊", "doctorName": "医生D"},
    ]

    result = build_recent_visits(items, limit=3)

    assert [item.visitId for item in result] == ["4", "2", "3"]
    assert result[0].department == "外科门诊"
    assert len(result) == 3
