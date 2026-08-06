"""SQLAlchemy 2.0 engine 与 session factory。

提供共享的 ``engine``、``SessionLocal`` 会话工厂，以及 FastAPI 依赖注入用的
``get_db()`` 生成器。所有持久层访问都应通过这里产出的 session 进行。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# 模块级单例引擎，连接池由 SQLAlchemy 管理。
engine: Engine = create_engine(settings.mysql_url, pool_pre_ping=True, future=True)

# 会话工厂：每次调用产出独立的 Session。
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=Session
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：产出 DB session 并在请求结束后关闭。

    Usage::

        @router.get("/")
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
