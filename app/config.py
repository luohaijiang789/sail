"""SAIL 配置。从环境变量读取。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- 基础设施 ---
    mysql_url: str = "mysql+pymysql://sail:sail@localhost:3306/sail"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "sail"
    minio_secret_key: str = "sail123456"
    minio_bucket: str = "sail"

    # --- CodeQL ---
    codeql_cli_path: str = "codeql"
    workspace_root: str = "/workspaces"

    # --- LLM ---
    llm_provider: str = "openai"
    llm_model_strong: str = "gpt-4o"
    llm_model_fast: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # --- 平台 ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    class Config:
        env_prefix = "SAIL_"
        env_file = ".env"


settings = Settings()
