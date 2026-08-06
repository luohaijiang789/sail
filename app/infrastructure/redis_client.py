"""Redis 客户端。

封装 SAIL 使用的 Redis 操作：缓存、SSE 事件流（pub/sub）、分布式锁。
实例在模块加载时按 ``settings.redis_url`` 建立连接。
"""

from typing import Any

from redis import Redis
from redis.lock import Lock

from app.config import settings

# 模块级单例客户端，连接由连接池管理。
redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def get(key: str) -> str | None:
    """读取键值，不存在返回 None。"""
    raise NotImplementedError


def set(key: str, value: Any, ex: int | None = None) -> bool:
    """写入键值，可选过期秒数。"""
    raise NotImplementedError


def publish(channel: str, message: str) -> int:
    """向频道发布消息，返回接收订阅者数量。"""
    raise NotImplementedError


def lock(name: str, timeout: int | None = None) -> Lock:
    """获取分布式锁，返回可上下文管理的 Lock 对象。"""
    raise NotImplementedError
