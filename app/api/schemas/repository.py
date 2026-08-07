"""仓库相关 DTO。

对应 ``app.domain.source_assets.Repository``。输入 DTO 用于创建/更新校验，
输出 DTO 用 ``from_attributes=True`` 直接从 ORM 实例转换，路由层不返回 ORM 对象。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryCreate(BaseModel):
    """创建仓库入参。"""

    name: str = Field(..., max_length=200, description="仓库名")
    git_url: str = Field(..., max_length=500, description="Git 远端地址")
    default_branch: str = Field(default="main", max_length=100, description="默认分支")
    project_id: int = Field(..., description="所属项目 ID")
    credential_id: str | None = Field(default=None, max_length=100, description="凭证标识")
    repository_type: str = Field(default="git", max_length=20, description="仓库类型，默认 git")


class RepositoryUpdate(BaseModel):
    """更新仓库入参，所有字段可选。"""

    name: str | None = Field(default=None, max_length=200)
    git_url: str | None = Field(default=None, max_length=500)
    default_branch: str | None = Field(default=None, max_length=100)
    credential_id: str | None = Field(default=None, max_length=100)
    repository_type: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=20)


class RepositoryOut(BaseModel):
    """仓库完整输出。含 id、状态、最近扫描 commit 与时间戳。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    git_url: str
    default_branch: str
    credential_id: str | None
    repository_type: str
    last_scanned_commit: str | None
    status: str
    project_name: str | None = None
    last_scan_status: str | None = None
    api_asset_count: int = 0
    high_risk_count: int = 0
    created_at: datetime


class RepositoryValidateOut(BaseModel):
    """仓库可达性校验结果。"""

    valid: bool = Field(..., description="是否可达")
    message: str = Field(default="", description="校验说明，失败时含原因")
