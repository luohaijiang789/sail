"""API 资产模型：api_asset + api_call_edge + api_resource_access + api_security_control。
对应架构文档 03-api-asset.md。
"""

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain import Base, TimestampMixin


class ApiAsset(Base, TimestampMixin):
    __tablename__ = "api_asset"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repository.id"), nullable=False)
    source_revision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("source_revision.id"), nullable=False)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # L1 字段（轻量层产出）
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    full_path: Mapped[str | None] = mapped_column(String(500))
    framework: Mapped[str] = mapped_column(String(30), nullable=False)
    controller_class: Mapped[str] = mapped_column(String(200), nullable=False)
    handler_method: Mapped[str] = mapped_column(String(100), nullable=False)
    handler_signature: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    consumes: Mapped[str | None] = mapped_column(String(50))
    produces: Mapped[str | None] = mapped_column(String(50))
    parameters_json: Mapped[dict | None] = mapped_column(JSON)
    response_type: Mapped[str | None] = mapped_column(String(200))
    declared_exceptions: Mapped[str | None] = mapped_column(Text)
    module: Mapped[str | None] = mapped_column(String(100))
    api_group: Mapped[str | None] = mapped_column(String(100))
    commit_author: Mapped[str | None] = mapped_column(String(100))
    commit_time: Mapped[str | None] = mapped_column(String(50))
    # L2 字段（深度层补充）
    call_chain_depth: Mapped[int | None] = mapped_column(Integer)
    enrichment_status: Mapped[str] = mapped_column(String(20), default="INITIAL")
    # 版本追踪
    first_seen_scan_id: Mapped[int | None] = mapped_column(BigInteger)
    last_seen_scan_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="NEW")  # NEW/ACTIVE/REMOVED/CHANGED


class ApiCallEdge(Base, TimestampMixin):
    __tablename__ = "api_call_edge"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    api_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_asset.id"), nullable=False, index=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    caller_symbol: Mapped[str] = mapped_column(String(500), nullable=False)
    caller_file: Mapped[str | None] = mapped_column(String(500))
    caller_line: Mapped[int | None] = mapped_column(Integer)
    callee_symbol: Mapped[str] = mapped_column(String(500), nullable=False)
    callee_file: Mapped[str | None] = mapped_column(String(500))
    callee_line: Mapped[int | None] = mapped_column(Integer)
    callee_type: Mapped[str] = mapped_column(String(20), default="INTERNAL")  # INTERNAL/LIBRARY/UNKNOWN
    edge_kind: Mapped[str] = mapped_column(String(20), default="DIRECT_CALL")
    parent_edge_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("api_call_edge.id"))
    path_signature: Mapped[str | None] = mapped_column(Text)


class ApiResourceAccess(Base, TimestampMixin):
    __tablename__ = "api_resource_access"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    api_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_asset.id"), nullable=False, index=True)
    call_edge_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("api_call_edge.id"))
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    source_layer: Mapped[str] = mapped_column(String(20), nullable=False)  # L1_DECLARED / L2_CALLCHAIN
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)  # DB_TABLE/SQL_QUERY/HTTP_OUTBOUND/...
    resource_name: Mapped[str] = mapped_column(String(200), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)  # READ/WRITE/DELETE/EXECUTE
    detail_json: Mapped[dict | None] = mapped_column(JSON)
    file_path: Mapped[str | None] = mapped_column(String(500))
    line: Mapped[int | None] = mapped_column(Integer)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)


class ApiSecurityControl(Base, TimestampMixin):
    __tablename__ = "api_security_control"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    api_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_asset.id"), nullable=False, index=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    control_type: Mapped[str] = mapped_column(String(30), nullable=False)  # AUTHN/AUTHZ/PARAM_VALIDATION/...
    control_method: Mapped[str] = mapped_column(String(100), nullable=False)
    control_value: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(String(20), default="ENDPOINT")  # ENDPOINT/METHOD/PARAM/GLOBAL
    file_path: Mapped[str | None] = mapped_column(String(500))
    line: Mapped[int | None] = mapped_column(Integer)
    enforced: Mapped[bool] = mapped_column(Boolean, default=True)
