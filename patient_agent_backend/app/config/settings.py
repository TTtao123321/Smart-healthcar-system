from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    app_name: str = "patient-agent-backend"
    debug: bool = False

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

    # 对话记忆
    max_conversation_turns: int = 20

    # 安全护栏
    max_unanswered_turns: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
