"""基础设施层接口定义（Protocol）。

用 typing.Protocol 定义抽象接口，基础设施实现这些接口。
好处：可替换、可测试（mock）、不依赖具体实现。
"""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GitClient(Protocol):
    """Git 操作接口。"""

    def clone_shallow(self, repo_url: str, branch: str, dest: str,
                      credential: str | None = None) -> str:
        """浅克隆，返回 commit_sha。"""
        ...

    def fetch_commit(self, repo_url: str, commit_sha: str, dest: str,
                     credential: str | None = None) -> None:
        """拉取指定 commit。"""
        ...

    def get_commit_info(self, dest: str) -> dict[str, Any]:
        """获取 commit 信息（sha/author/time/message）。"""
        ...


@runtime_checkable
class ObjectStorage(Protocol):
    """对象存储接口（MinIO/S3 兼容）。"""

    def upload_file(self, bucket: str, key: str, file_path: str,
                    content_type: str | None = None) -> dict[str, Any]:
        """上传文件，返回元数据。"""
        ...

    def download_file(self, bucket: str, key: str, dest_path: str) -> None:
        """下载文件到本地。"""
        ...

    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        """获取预签名下载 URL。"""
        ...

    def stream_upload(self, bucket: str, key: str, stream: Any,
                      size: int | None = None) -> dict[str, Any]:
        """流式上传（构建日志实时上传用）。"""
        ...

    def delete_object(self, bucket: str, key: str) -> None:
        """删除对象。"""
        ...


@runtime_checkable
class CodeQLClient(Protocol):
    """CodeQL CLI 接口。"""

    def create_database(self, db_path: str, language: str,
                        build_command: list[str] | None,
                        source_root: str, build_mode: str = "MANUAL") -> dict[str, Any]:
        """创建 CodeQL 数据库。"""
        ...

    def analyze_database(self, db_path: str, query_pack: str,
                         output_sarif_path: str) -> str:
        """分析数据库，输出 SARIF。"""
        ...

    def get_database_info(self, db_path: str) -> dict[str, Any]:
        """获取数据库信息（文件数/语言/质量）。"""
        ...

    def run_query(self, db_path: str, query_file: str,
                  output_format: str = "csv") -> str:
        """运行单个 QL 查询（API 信息补全用）。"""
        ...


@runtime_checkable
class CacheClient(Protocol):
    """缓存/锁接口（Redis）。"""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: int | None = None) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def acquire_lock(self, key: str, ttl: int = 300) -> bool: ...
    def release_lock(self, key: str) -> bool: ...
    def publish(self, channel: str, message: str) -> int: ...
    def subscribe(self, channel: str) -> Any: ...


@runtime_checkable
class LlmProvider(Protocol):
    """LLM 调用接口。可被 OpenAI/Anthropic/其他实现。"""

    def chat(self, prompt: str, model: str, temperature: float = 0.2,
             max_tokens: int = 16384, response_format: dict | None = None) -> dict[str, Any]:
        """调用 LLM，返回 {content, input_tokens, output_tokens, cost_usd, model}。"""
        ...

    def chat_with_retry(self, prompt: str, model: str, temperature: float = 0.2,
                        max_retries: int = 3) -> dict[str, Any]:
        """调用 LLM，带限流重试。"""
        ...
