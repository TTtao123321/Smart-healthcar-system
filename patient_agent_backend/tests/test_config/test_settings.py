import pytest

from app.config.settings import Settings


def test_settings_parse_cors_origins_from_csv(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://a.example.com,https://b.example.com",
    )
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")

    settings = Settings()

    assert settings.app_env == "production"
    assert settings.cors_allowed_origins == [
        "https://a.example.com",
        "https://b.example.com",
    ]
    assert settings.cors_allow_credentials is True


def test_settings_rejects_wildcard_origin_with_credentials_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")

    with pytest.raises(ValueError):
        Settings()


def test_settings_parse_patient_agent_e2e_flags(monkeypatch):
    monkeypatch.setenv("PATIENT_AGENT_E2E_MODE", "true")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PHONE", "13800138000")
    monkeypatch.setenv("PATIENT_AGENT_E2E_CODE", "123456")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PATIENT_ID", "12")
    monkeypatch.setenv("PATIENT_AGENT_E2E_PATIENT_NAME", "张三")

    settings = Settings()

    assert settings.patient_agent_e2e_mode is True
    assert settings.patient_agent_e2e_phone == "13800138000"
    assert settings.patient_agent_e2e_code == "123456"
    assert settings.patient_agent_e2e_patient_id == 12
    assert settings.patient_agent_e2e_patient_name == "张三"
