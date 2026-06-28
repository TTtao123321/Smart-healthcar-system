from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    app_name: str = "patient-agent-backend"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    cors_allowed_origins: list[str] | str = "http://localhost:5173"
    cors_allow_credentials: bool = True
    sms_return_code_dev: bool = True

    # HMS API
    hms_api_url: str = "http://localhost:8080"
    hms_api_timeout: float = 10.0

    # HMS MySQL
    hms_db_host: str = "127.0.0.1"
    hms_db_port: int = 3306
    hms_db_name: str = "hospital"
    hms_db_user: str = "root"
    hms_db_password: str = ""

    # HMS 管理端认证（用于调用需要 SaToken 的接口）
    hms_admin_username: str = "admin"
    hms_admin_password: str = ""

    # OpenAI / LLM
    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Redis
    redis_url: str = "redis://localhost:6379/1"
    flow_state_ttl_seconds: int = 60 * 60 * 24

    # patient_agent 页面级 E2E
    patient_agent_e2e_mode: bool = False
    patient_agent_e2e_phone: str = "13800138000"
    patient_agent_e2e_code: str = "123456"
    patient_agent_e2e_patient_id: int = 12
    patient_agent_e2e_patient_name: str = "张三"

    # 对话记忆
    max_conversation_turns: int = 20

    # 安全护栏
    max_unanswered_turns: int = 3

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value):
        if value is None or value == "":
            return ["http://localhost:5173"]
        if isinstance(value, str):
            if value == "*":
                return ["*"]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_cors(self):
        if (
            self.app_env == "production"
            and self.cors_allow_credentials
            and "*" in self.cors_allowed_origins
        ):
            raise ValueError("生产环境不允许在开启凭证时使用通配符 CORS")
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
