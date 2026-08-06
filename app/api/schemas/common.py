"""通用查询参数 DTO：分页与排序。

所有列表路由共用，避免每个 router 重复定义 page/page_size/sort_by/sort_order。
"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """分页参数。``page`` 从 1 起，``page_size`` 默认 20、上限 100。"""

    page: int = Field(default=1, ge=1, description="页码，从 1 起")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，1-100")


class SortParams(BaseModel):
    """排序参数。``sort_order`` 仅 ``asc`` / ``desc``。"""

    sort_by: str | None = Field(default=None, description="排序字段名")
    sort_order: str = Field(default="asc", description="asc 或 desc")
