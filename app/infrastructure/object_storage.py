"""MinIO 对象存储客户端。

封装源码归档、CodeQL 数据库缓存、构建日志、SARIF 等制品的上传下载与预签名 URL。
存储路径约定见 docs/02-build.md「对象存储路径」一节。
"""

from typing import Any

from minio import Minio

from app.config import settings

# 模块级单例客户端。
minio_client: Minio = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def upload_file(bucket: str, key: str, path: str) -> dict[str, Any]:
    """上传本地文件到 ``bucket/key``，返回制品元数据。

    Returns:
        包含 storage_key、file_name、size_bytes、content_type、checksum_sha256 的字典。
    """
    raise NotImplementedError


def download_file(bucket: str, key: str, path: str) -> None:
    """从 ``bucket/key`` 下载对象到本地 ``path``。"""
    raise NotImplementedError


def get_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    """生成可临时访问 ``bucket/key`` 的预签名 GET URL。"""
    raise NotImplementedError
