"""API Schema 层：Pydantic DTO 集合。

本包是 API 层与 ORM 的解耦边界——路由入参/出参一律用这里的 DTO，
不直接返回 ORM 对象。所有输出 DTO 设 ``from_attributes=True``，
便于 ``RepositoryOut.model_validate(orm_instance)`` 直接转换。

按子域分模块：
- ``common``：分页/排序参数
- ``repository``：仓库 CRUD
- ``scan``：扫描创建、状态、阶段、日志、事件
- ``api_asset``：API 资产详情、调用链、安全画像、check 矩阵、历史
- ``finding``：漏洞列表、详情、实例、证据、数据流
- ``feedback``：人工反馈提交与分析结果
"""

from app.api.schemas.api_asset import (
    ApiAssetHistoryOut,
    ApiAssetListOut,
    ApiAssetOut,
    CallEdgeOut,
    CheckOut,
    ResourceAccessOut,
    SecurityControlOut,
    SecurityProfileOut,
)
from app.api.schemas.common import PaginationParams, SortParams
from app.api.schemas.feedback import FeedbackCreate, FeedbackOut
from app.api.schemas.finding import (
    DataflowOut,
    EvidenceOut,
    FindingInstanceOut,
    FindingListOut,
    FindingOut,
    FindingStatusUpdate,
)
from app.api.schemas.repository import (
    RepositoryCreate,
    RepositoryOut,
    RepositoryUpdate,
    RepositoryValidateOut,
)
from app.api.schemas.scan import (
    RevisionRef,
    ScanCreate,
    ScanEventOut,
    ScanLogOut,
    ScanOut,
    StageOut,
)

__all__ = [
    # common
    "PaginationParams",
    "SortParams",
    # repository
    "RepositoryCreate",
    "RepositoryUpdate",
    "RepositoryOut",
    "RepositoryValidateOut",
    # scan
    "RevisionRef",
    "ScanCreate",
    "ScanOut",
    "StageOut",
    "ScanLogOut",
    "ScanEventOut",
    # api_asset
    "ApiAssetOut",
    "ApiAssetListOut",
    "CallEdgeOut",
    "ResourceAccessOut",
    "SecurityControlOut",
    "CheckOut",
    "SecurityProfileOut",
    "ApiAssetHistoryOut",
    # finding
    "FindingOut",
    "FindingInstanceOut",
    "FindingListOut",
    "EvidenceOut",
    "DataflowOut",
    "FindingStatusUpdate",
    # feedback
    "FeedbackCreate",
    "FeedbackOut",
]
