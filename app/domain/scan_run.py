"""ScanRun / ScanStageRun 模型。对应架构文档 08-orchestration.md。"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain import Base, TimestampMixin

# ScanRun 状态
SCAN_RUN_CREATED = "CREATED"
SCAN_RUN_QUEUED = "QUEUED"
SCAN_RUN_RUNNING = "RUNNING"
SCAN_RUN_SUCCEEDED = "SUCCEEDED"
SCAN_RUN_PARTIAL_SUCCEEDED = "PARTIAL_SUCCEEDED"
SCAN_RUN_FAILED = "FAILED"
SCAN_RUN_CANCELLED = "CANCELLED"

# ScanStageRun 状态
STAGE_PENDING = "PENDING"
STAGE_RUNNING = "RUNNING"
STAGE_SUCCEEDED = "SUCCEEDED"
STAGE_FAILED_RETRYABLE = "FAILED_RETRYABLE"
STAGE_FAILED_FINAL = "FAILED_FINAL"
STAGE_SKIPPED = "SKIPPED"
STAGE_CANCELLED = "CANCELLED"
STAGE_TIMEOUT = "TIMEOUT"

# 阶段类型
STAGE_FETCH_SOURCE = "FETCH_SOURCE"
STAGE_PREFLIGHT = "PREFLIGHT"
STAGE_BUILD_CODEQL_DATABASE = "BUILD_CODEQL_DATABASE"
STAGE_EXTRACT_API_FACTS = "EXTRACT_API_FACTS"
STAGE_ENRICH_API_DEPTH = "ENRICH_API_DEPTH"
STAGE_RUN_CODEQL_VULN_SCAN = "RUN_CODEQL_VULN_SCAN"
STAGE_FINDING_CANDIDATES = "FINDING_CANDIDATES"
STAGE_ASSEMBLE_CONTEXT = "ASSEMBLE_CONTEXT"
STAGE_AI_ANALYZE = "AI_ANALYZE"
STAGE_MERGE_FINDINGS = "MERGE_FINDINGS"
STAGE_ASSESS_API_SECURITY = "ASSESS_API_SECURITY"
STAGE_PERSIST_RESULTS = "PERSIST_RESULTS"
STAGE_FINALIZE = "FINALIZE"


class ScanRun(Base, TimestampMixin):
    __tablename__ = "scan_run"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("project.id"), nullable=False)
    repository_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repository.id"), nullable=False)
    source_revision_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("source_revision.id"))
    scan_profile_id: Mapped[int | None] = mapped_column(BigInteger)
    trigger_type: Mapped[str] = mapped_column(String(20), default="MANUAL")
    status: Mapped[str] = mapped_column(String(20), default=SCAN_RUN_CREATED, index=True)
    current_stage: Mapped[str | None] = mapped_column(String(40))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    build_quality: Mapped[str | None] = mapped_column(String(30))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String(100))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_code: Mapped[str | None] = mapped_column(String(50))
    failure_message: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(20), default="FULL")  # FULL / INCREMENTAL
    base_scan_run_id: Mapped[int | None] = mapped_column(BigInteger)


class ScanStageRun(Base, TimestampMixin):
    __tablename__ = "scan_stage_run"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False, index=True)
    stage_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=STAGE_PENDING)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    on_failure: Mapped[str] = mapped_column(String(20), default="ABORT")  # ABORT/DEGRADE/CONTINUE
    celery_task_id: Mapped[str | None] = mapped_column(String(100))
    input_fingerprint: Mapped[str | None] = mapped_column(String(64))
    output_artifact_id: Mapped[int | None] = mapped_column(BigInteger)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    retryable: Mapped[bool | None] = mapped_column(Boolean)
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)
    metrics_json: Mapped[dict | None] = mapped_column(JSON)


# 阶段定义：required + on_failure（对应 08-orchestration.md 阶段表）
STAGE_DEFINITIONS: dict[str, dict] = {
    STAGE_FETCH_SOURCE: {"required": True, "on_failure": "ABORT"},
    STAGE_PREFLIGHT: {"required": True, "on_failure": "ABORT"},
    STAGE_BUILD_CODEQL_DATABASE: {"required": True, "on_failure": "DEGRADE"},
    STAGE_EXTRACT_API_FACTS: {"required": True, "on_failure": "ABORT"},
    STAGE_ENRICH_API_DEPTH: {"required": False, "on_failure": "CONTINUE"},
    STAGE_RUN_CODEQL_VULN_SCAN: {"required": True, "on_failure": "ABORT"},
    STAGE_FINDING_CANDIDATES: {"required": True, "on_failure": "ABORT"},
    STAGE_ASSEMBLE_CONTEXT: {"required": False, "on_failure": "CONTINUE"},
    STAGE_AI_ANALYZE: {"required": False, "on_failure": "CONTINUE"},
    STAGE_MERGE_FINDINGS: {"required": True, "on_failure": "ABORT"},
    STAGE_ASSESS_API_SECURITY: {"required": False, "on_failure": "CONTINUE"},
    STAGE_PERSIST_RESULTS: {"required": True, "on_failure": "ABORT"},
    STAGE_FINALIZE: {"required": True, "on_failure": "ABORT"},
}

# 阶段依赖（DAG）：每个阶段的上游阶段
STAGE_DEPENDENCIES: dict[str, list[str]] = {
    STAGE_FETCH_SOURCE: [],
    STAGE_PREFLIGHT: [STAGE_FETCH_SOURCE],
    STAGE_BUILD_CODEQL_DATABASE: [STAGE_PREFLIGHT],
    STAGE_EXTRACT_API_FACTS: [STAGE_BUILD_CODEQL_DATABASE],
    STAGE_ENRICH_API_DEPTH: [STAGE_EXTRACT_API_FACTS],
    STAGE_RUN_CODEQL_VULN_SCAN: [STAGE_BUILD_CODEQL_DATABASE],
    STAGE_FINDING_CANDIDATES: [STAGE_RUN_CODEQL_VULN_SCAN],
    STAGE_ASSEMBLE_CONTEXT: [STAGE_FINDING_CANDIDATES, STAGE_EXTRACT_API_FACTS],
    STAGE_AI_ANALYZE: [STAGE_ASSEMBLE_CONTEXT],
    STAGE_MERGE_FINDINGS: [STAGE_AI_ANALYZE, STAGE_FINDING_CANDIDATES],
    STAGE_ASSESS_API_SECURITY: [STAGE_MERGE_FINDINGS],
    STAGE_PERSIST_RESULTS: [STAGE_ASSESS_API_SECURITY, STAGE_MERGE_FINDINGS],
    STAGE_FINALIZE: [STAGE_PERSIST_RESULTS],
}
