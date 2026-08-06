"""SAIL 测试配置。"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def db_session():
    """数据库 session fixture。第一阶段用内存 SQLite，后续换 test MySQL。"""
    # TODO: 配置测试数据库
    yield
