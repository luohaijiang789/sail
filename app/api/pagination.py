"""SQLAlchemy query 分页工具。

把 ``PaginationParams`` 应用到任意 SQLAlchemy ``select`` / ``query``，
返回统一的 ``PaginatedResult``。列表路由复用本函数，避免每处手写 limit/offset。
"""

from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.common import PaginationParams
from app.core.result import PaginatedResult

T = TypeVar("T")


def paginate(db: Session, stmt: select, params: PaginationParams) -> PaginatedResult[T]:
    """对 SQLAlchemy ``select`` 语句分页。

    Args:
        db: SQLAlchemy session，用于执行 count 与 slice。
        stmt: ``select(Model)`` 或带 filter/order_by 的语句。
        params: 分页参数（page 从 1 起）。

    Returns:
        ``PaginatedResult``，含 items / total / page / page_size / has_next。

    Note:
        count 子查询复用原语句的 where 条件，不重复构造过滤逻辑。
        ``page`` 已由 ``PaginationParams`` 校验 >=1，``page_size`` 校验 1-100。
    """
    page = params.page
    page_size = params.page_size

    # count 复用原语句的 where 条件
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    items = list(db.execute(stmt.offset(offset).limit(page_size)).scalars().all())

    has_next = (offset + page_size) < total
    return PaginatedResult[T](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )


def paginate_models(items: list[T], total: int, params: PaginationParams) -> PaginatedResult[T]:
    """对已在内存中的列表分页（如聚合后的非 ORM 结果）。

    适用于无法直接用 SQL 分页的场景：先取全量再切片。生产环境慎用大结果集。
    """
    page = params.page
    page_size = params.page_size
    offset = (page - 1) * page_size
    sliced = items[offset : offset + page_size]
    has_next = (offset + page_size) < total
    return PaginatedResult[T](
        items=sliced,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )
