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
