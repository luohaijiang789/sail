"""SAIL 配置。从环境变量读取。"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- 基础设施 ---
    # 本地开发默认 SQLite，生产用 MySQL（docker-compose 注入 SAIL_MYSQL_URL）
    mysql_url: str = f"sqlite:///{Path('./sail.db').absolute()}"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "sail"
    minio_secret_key: str = "sail123456"
    minio_bucket: str = "sail"

    # --- CodeQL ---
    codeql_cli_path: str = "codeql"
    workspace_root: str = "/tmp/sail-workspaces"

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

