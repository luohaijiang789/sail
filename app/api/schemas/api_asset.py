"""API 资产相关 DTO。

对应 ``app.domain.api_asset`` 与 ``app.domain.check_and_security`` 模型。
涵盖资产详情、调用链边、资源访问、安全控制、check 矩阵、安全画像与版本历史。

输出 DTO 设 ``from_attributes=True`` 以支持从 ORM 实例转换；列表精简版只暴露
列表视图所需字段，避免大表全量序列化。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiAssetOut(BaseModel):
    """API 资产完整输出：L1 入口字段 + L2 深度字段 + 版本追踪字段。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    source_revision_id: int
    scan_run_id: int
    fingerprint: str
    # L1 字段
    http_method: str
    path: str
    full_path: str | None
    framework: str
    controller_class: str
    handler_method: str
    handler_signature: str | None
    file_path: str
    start_line: int | None
    end_line: int | None
    consumes: str | None
    produces: str | None
    parameters_json: dict | None
    response_type: str | None
    declared_exceptions: str | None
    module: str | None
    api_group: str | None
    commit_author: str | None
    commit_time: str | None
    # L2 字段
    call_chain_depth: int | None
    enrichment_status: str
    # 版本追踪
    first_seen_scan_id: int | None
    last_seen_scan_id: int | None
    status: str
    created_at: datetime


class ApiAssetListOut(BaseModel):
    """API 资产列表精简版：方法/路径/控制器/安全分/漏洞数/状态。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    http_method: str
    path: str
    controller_class: str
    overall_score: int | None = Field(default=None, description="安全画像总分，无画像时为 None")
    finding_count: int = Field(default=0, description="关联漏洞数")
    status: str


class CallEdgeOut(BaseModel):
    """调用链边。对应 ``ApiCallEdge``，已扁平化以便前端渲染树/图。"""

    model_config = ConfigDict(from_attributes=True)

    depth: int
    caller: str = Field(..., description="调用方符号")
    callee: str = Field(..., description="被调用方符号")
    file: str | None = Field(default=None, description="调用发生文件")
    line: int | None = Field(default=None, description="调用发生行号")
    edge_kind: str = Field(default="DIRECT_CALL", description="边类型")


class ResourceAccessOut(BaseModel):
    """资源访问项。对应 ``ApiResourceAccess``。"""

    model_config = ConfigDict(from_attributes=True)

    resource_type: str = Field(..., description="DB_TABLE/SQL_QUERY/HTTP_OUTBOUND 等")
    resource_name: str
    operation: str = Field(..., description="READ/WRITE/DELETE/EXECUTE")
    is_sensitive: bool = False


class SecurityControlOut(BaseModel):
    """安全控制项。对应 ``ApiSecurityControl``。"""

    model_config = ConfigDict(from_attributes=True)

    control_type: str = Field(..., description="AUTHN/AUTHZ/PARAM_VALIDATION 等")
    control_method: str
    control_value: str | None = None
    scope: str = Field(default="ENDPOINT", description="ENDPOINT/METHOD/PARAM/GLOBAL")
    enforced: bool = True


class CheckOut(BaseModel):
    """check 矩阵单项。对应 ``ApiCheck`` 的对外视图。"""

    model_config = ConfigDict(from_attributes=True)

    check_item_key: str = Field(..., description="检查项标识，如 SQL_INJECTION/NO_AUTHN")
    check_item_name: str
    result: str = Field(..., description="PASS/LOW/MEDIUM/HIGH/CRITICAL/NOT_CHECKED")
    evidence_summary: str | None = None


class SecurityProfileOut(BaseModel):
    """安全画像。对应 ``ApiSecurityProfile``。"""

    model_config = ConfigDict(from_attributes=True)

    overall_score: int = Field(..., description="总分 0-100，分高=危险")
    overall_level: str = Field(..., description="SAFE/LOW_RISK/.../CRITICAL")
    exposure_score: int
    callchain_score: int
    data_sensitivity_score: int
    codequality_score: int
    check_coverage: int = Field(default=0, description="已检查项数占比 * 100")
    blind_spots: list[str] | None = Field(default=None, description="未检查项列表")


class ApiAssetHistoryOut(BaseModel):
    """API 资产版本历史项：某次扫描中的安全分/级别/变化类型。"""

    model_config = ConfigDict(from_attributes=True)

    commit_sha: str
    commit_time: datetime | None
    overall_score: int
    overall_level: str
    change_type: str = Field(..., description="NEW/ACTIVE/REMOVED/CHANGED")
