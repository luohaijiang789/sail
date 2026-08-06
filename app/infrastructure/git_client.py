"""Git 操作封装。

封装浅克隆、按 commit 拉取、commit 信息读取，供 FETCH_SOURCE 阶段使用。
凭证按 ``credential`` 参数透传，避免在 worker 进程中泄露密钥。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommitInfo:
    """Git commit 摘要信息。"""

    sha: str
    author: str
    time: datetime
    message: str


def clone_shallow(repo_url: str, branch: str, dest: str, credential: str | None = None) -> str:
    """浅克隆 ``repo_url`` 的 ``branch`` 到 ``dest``，返回解析出的 commit_sha。

    Args:
        repo_url: 仓库 URL（git/https）。
        branch: 分支名。
        dest: 本地目标目录。
        credential: 可选凭证标识，用于私密仓库拉取。

    Returns:
        钉死的 commit_sha，对应 SourceRevision.commit_sha。
    """
    raise NotImplementedError


def fetch_commit(repo_url: str, commit_sha: str, dest: str, credential: str | None = None) -> None:
    """按指定 commit 拉取到 ``dest``（``git fetch --depth 1 origin <sha>``）。"""
    raise NotImplementedError


def get_commit_info(dest: str) -> CommitInfo:
    """读取 ``dest`` 工作区当前 HEAD 的 commit 摘要信息。"""
    raise NotImplementedError
