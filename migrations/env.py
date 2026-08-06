"""Alembic 迁移环境。"""

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.domain import Base
# 导入所有模型确保 Alembic 能发现
from app.domain import source_assets, scan_run, api_asset, check_and_security, finding  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.mysql_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config = {"sqlalchemy.url": settings.mysql_url}
    connectable = engine_from_config(config, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
